from iqoptionapi.stable_api import IQ_Option
from datetime import datetime, timedelta
from os import system
import threading
import time
import sys



# ------------------- CONSTANTES

#PAYOUTS = { 'digital': {}, 'turbo': {} }
EMAIL = ''
SENHA = ''
BALANCE = 'PRACTICE' # practice/real
TIPO = 'turbo' # turbo/digital
GET_CANDLES_TIMEFRAME = 60
BUY_TIMEFRAME = 1
PERIDO = 3



# ------------------- TODAS AS VARIÁVEIS GLOBAIS

api = None
par = ''
hora_inicio = ''
entrada_base = 0
banca_inicio = 0.0
conectado = False



# ------------------- FUNÇÕES

def IniciarThreadChecarConexao():
	thread = threading.Thread(target=ChecarConexao)
	thread.daemon = True
	thread.start()

def ChecarConexao():
	global conectado

	while True:
		if api.check_connect() == False:
			PrintarTentandoReconectar()

			conectado = False
			api.connect()
		else:
			conectado = True
		
		time.sleep(15)

#def IniciarThreadAtualizarPayout():
	#thread = threading.Thread(target=AtualizarPayouts)
	#thread.daemon = True
	#thread.start()

#def AtualizarPayouts():
	#while True:
		#tipos = ['turbo']
		#pares = api.get_all_open_time()
		
		#for tipo in tipos:
			#for par in pares[tipo]:
				#if pares[tipo][par]['open'] == True:
					#PAYOUTS[tipo].update({ par: Payout(par) })

		#time.sleep(30)

def Hora(): 
	return datetime.now().strftime('%H:%M:%S:%f')

def Banca():
	return api.get_balance()

def Payout():
	if TIPO == 'turbo':
		a = api.get_all_profit()

		return int(100 * a[par]['turbo'])
	elif TIPO == 'digital':
		api.subscribe_strike_list(par, 1)

		while True:
			d = api.get_digital_current_profit(par, 1)
			if d != False:
				break

			time.sleep(1)

		api.unsubscribe_strike_list(par, 1)

		return d

def SegundosFloat():
	return float(datetime.now().strftime('%S.%f'))

def HoraDeEntrar():
	minutos = datetime.now().strftime('%M.%S')
	minutos_float = float(minutos[1:])
	ok = minutos_float == 5.00 or minutos_float == 0.00

	return ok

def DelayAceitavel():
	segundos = int(datetime.now().strftime('%S'))
	ok = segundos >= 0 and segundos <= 3

	return ok

def TransformarVelasEmCores(velas):
	velas[0] = 'g' if velas[0]['open'] < velas[0]['close'] else 'r' if velas[0]['open'] > velas[0]['close'] else 'd'
	velas[1] = 'g' if velas[1]['open'] < velas[1]['close'] else 'r' if velas[1]['open'] > velas[1]['close'] else 'd'
	velas[2] = 'g' if velas[2]['open'] < velas[2]['close'] else 'r' if velas[2]['open'] > velas[2]['close'] else 'd'

def Direcao(str_cores_velas):
	direcao = False	
	if str_cores_velas.count('g') > str_cores_velas.count('r') and str_cores_velas.count('d') == 0: 
		direcao = 'put'
	if str_cores_velas.count('r') > str_cores_velas.count('g') and str_cores_velas.count('d') == 0: 
		direcao = 'call'	

	return direcao

def Stop(valor_resultante, mhi_count, lucro):
	if valor_resultante < 0:
		PrintarStop('************* STOP LOSS *************', mhi_count, lucro)
		sys.exit()
	elif mhi_count == 2:
		PrintarStop('************* STOP GAIN *************', mhi_count, lucro)
		sys.exit()

def CheckResult(id, lucro, mhi_count, delay, payout):
	while True: 
		valor_resultante = api.check_win_v3(id)

		lucro += valor_resultante

		PrintarResultado(valor_resultante, lucro, delay, payout)
		Stop(valor_resultante, mhi_count, lucro)
		
		return lucro

def Operar(direcao, entrada, lucro, mhi_count, segundos_inicio):
	if DelayAceitavel():
		status, id = api.buy(entrada, par, direcao, BUY_TIMEFRAME)
		delay = SegundosFloat() - segundos_inicio

		payout = Payout()

		if status:
			lucro = CheckResult(id, lucro, mhi_count, delay, payout)
			entrada += lucro
		else:
			PrintarErroOperacao()
	else:
		PrintDelayInaceitavel()

	return (entrada, lucro)

def IniciarMHI():
	PrintarInicio()

	entrada = entrada_base
	lucro = 0
	mhi_count = 0

	while True:
		if HoraDeEntrar() and conectado:
			segundos_inicio = SegundosFloat()

			minuto_antes = datetime.now() - timedelta(minutes=1)
			velas = api.get_candles(par, GET_CANDLES_TIMEFRAME, PERIDO, datetime.timestamp(minuto_antes))

			TransformarVelasEmCores(velas)

			str_cores_velas = velas[0] + ' ' + velas[1] + ' ' + velas[2] 
			direcao = Direcao(str_cores_velas)

			if direcao:
				mhi_count += 1

				PrintarInicioMHI(str_cores_velas, direcao, entrada)

				entrada, lucro = Operar(direcao, entrada, lucro, mhi_count, segundos_inicio)
			else:
				PrintarDojiEncontrado()
				time.sleep(2.5)

	time.sleep(0.5)

def PrintarInicio():
	print('\n')
	print('Banca inicial: ' + str(Banca()))
	print('Esperando a primeira operação...')

	PrintarResumo()

def PrintarInicioMHI(str_cores_velas, direcao, entrada):
	print('\n')
	print('----- Iniciando MHI -----')
	print('DIREÇÃO:', direcao.upper(), '/ CORES:', str_cores_velas)
	print('ENTRADA:', round(entrada, 2))

	PrintarResumo()

def PrintarFalhaIniciarMHI():
	print('\n')
	print('************* NÃO INICIOU O MHI POR FALTA DE CONEXÃO *************')

	PrintarResumo()

def PrintarDojiEncontrado():
	print('\n')
	print('DOJI Encontrado! MHI abortado!')

	PrintarResumo()

def PrintarErroOperacao():
	print('\n')
	print('ERRO AO REALIZAR OPERAÇÃO!!!')

	PrintarResumo()

def PrintDelayInaceitavel():
	print('\n')
	print('A OPERAÇÃO FOI ABORTADA PORQUE JÁ PASSOU DA HORA DE ENTRAR!!!')

	PrintarResumo()

def PrintarTentandoReconectar():
	print('\n')
	print('************* TENTANDO RECONECTAR *************')

	PrintarResumo()

def PrintarResultado(valor_resultante, lucro, delay, payout):
	if payout:
		if valor_resultante > 0:
			str_result = '[WIN]'  
		elif valor_resultante < 0: 
			str_result = '[LOSS]'
		else:
			str_result = '[EMPATE]'

		print('\n')
		print('----- Resultado Operação -----')
		print(str_result, round(valor_resultante, 2), '/ PAYOUT:', str(round(payout, 2)) + '%', '/ LUCRO:', round(lucro, 2))
		print('DELAY:', delay)

		PrintarResumo()

def PrintarStop(título, mhi_count, lucro):
	print('\n')
	print(título)
	print('Tipo:', TIPO, '/ Par:', par)
	print('Entrada base:', str(entrada_base))
	print('Qtd. MHI realizado:', str(mhi_count))
	print('Banca inicial:', str(banca_inicio))
	print('Banca final:', str(Banca()))
	print('Lucro:', lucro)
	print('Hora de início:', hora_inicio)
	print('Hora de término:', Hora())

def PrintarResumo():
	print('Tipo: ' + TIPO + ' / Par: ' + par)
	print(Hora())

def PrintLog(msg):
	print('\n')
	print('Log [' + str(msg) + ']: ' + Hora())



# ------------------- MAIN

system('cls')
print('\n\n\n\n')

api = IQ_Option(EMAIL, SENHA)
api.connect()
api.change_balance(BALANCE)

par = input('Par: ').upper()

entrada_base = float(input('Entrada base: '))

hora_inicio = Hora()
banca_inicio = Banca()

IniciarThreadChecarConexao()
#IniciarThreadAtualizarPayout()
IniciarMHI()