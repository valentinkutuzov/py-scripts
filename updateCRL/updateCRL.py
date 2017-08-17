#! /opt/Python-3.5.3/python
#
# Программа для обновления справочника отозванных сертификатов:
# - скачивает файл с сайта ГПБ
# - 
# - 
# - 
# - отправляет протокол работы на telegram
import datetime, time, json, os, requests, re, traceback, logging, telebot
from _stat import filemode

#токен Бота
bot_token = '393803088:AAHVPkwYpCuurLhE0Kyt3cW8udsvGR4nLfg'

#номер секретного канала
channel_id = '-1001112920537'

# получаем текущую дату
currentDate = datetime.datetime.now().strftime('%d%m%Y')

#ссылка на СОС
urlCRL = 'http://cs.gazprombank.ru/crl/7cd42baf8043ecaa78e13c47f143b6716df2d091.crl'

#файл протокола
fileLog='/var/log/updateBIC/updateCRL.log'

#путь для сохранения файлов
destinationPath = '/var/www/updateBIC/<date>/'


def sendReport():
    
    theFile = open(fileLog,'r')
    
    bot=telebot.TeleBot(bot_token)
    bot.config['api_key'] = bot_token
    bot.send_message(channel_id, theFile.read())
    
    theFile.close()

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename=fileLog,
                    filemode='w')

logging.info('Starting CRL update...')

#Заменить в параметрах выражение <date> на сегодняшнюю дату
regexpTmp = re.compile(r'<date>')
destinationPath = regexpTmp.sub(currentDate, destinationPath)

#TODO: поключиться к странице Банка Росии
try:
    res=requests.get(urlCRL)
    res.raise_for_status()
except Exception as esc:
    logging.critical('Error fetching the CRL-file. Program aborted. \n %s' %traceback.format_exc())
    sendReport()
    exit()
else:
    logging.info(res.status_code)

#TODO: сохранение файлов в каталог назначения
#проверяем есть ли такой каталог, если нет, то создаем
if not os.path.exists(destinationPath):
    os.makedirs(destinationPath)
    logging.info('Directory created %s.' %destinationPath)
    
try:
    destinationFile = open(destinationPath+'/'+urlCRL.split('/')[-1],'wb')
except Exception as exc:
    logging.critical('File save error %s./n%s' %(destinationPath+'/'+urlCRL.split('/')[-1],traceback.format_exc()))
else:
    for chunk in res.iter_content(100000):
        destinationFile.write(chunk)
        
    destinationFile.close()
    logging.info('Download successful %s.' %(destinationPath+urlCRL.split('/')[-1]))

logging.info('Program terminated.')
sendReport()