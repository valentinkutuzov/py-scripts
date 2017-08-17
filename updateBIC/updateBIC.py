#! /opt/Python-3.5.3/python
#
# Программа для обновления справочников БИК:
# - читает файл с настройками
# - скачивает архив базы данных за текущее число
# - скачивает корректуру к базе данных за текущее число
# - сохраняет файлы в каталог YYYYMMDD сегодняшнего числа для web-сайта
# - отправляет протокол работы на почту, WhatsApp или telegram

import datetime, time, json, os, requests, bs4, re, traceback, logging, telebot
from _stat import filemode

#токен Бота
bot_token = '393803088:AAHVPkwYpCuurLhE0Kyt3cW8udsvGR4nLfg'

#номер секретного канала
channel_id = '-1001112920537'

# получаем текущую дату
currentDate = datetime.datetime.now().strftime('%d%m%Y')

#TODO: заполнить файл настроек данными / считать данные из файла настроек
#страница с сайта ЦБ РФ, где размещены корректура и обновление
baseURL = 'http://www.cbr.ru/mcirabis/?PrtId=bic'

#топ-страница сайта ЦБ РФ
baseURLTop = 'http://www.cbr.ru'

#уровень протоколирования
# 0  - не указан
# 10 - DEBUG
# 20 - INFO
# 30 - WARNING
# 40 - ERROR
# 50 - CRITICAL
loglevel = 20

#путь для сохранения файлов
destinationPath = '/var/www/updateBIC/<date>/'

#регулярные выражения для справочника БИК и корректуры
regexpBICDB = r'/mcirabis/BIK/bik_db_<date>.zip'
regexpBICUpdate = r'/mcirabis/BIK/bik_dc_\d+_<date>.zip'

#файл настроек
fileSettings = 'updateBIC.conf'

#файл протокола
fileLog='/var/log/updateBIC/updateBIC.log'

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

logging.info('Запуск программы')


#programSettings = {'baseURL':baseURL,
#                   'baseURLTop':baseURLTop,
#                   'loglevel':loglevel,
#                   'destinationPath':destinationPath,
#                   'regexpBICDB':regexpBICDB,
#                   'regexpBICUpdate':regexpBICUpdate}

#чтение файла с настройками и запись настроек в словарь
try:
 #   jsonFile = open(fileSettings,'w')
    logging.debug('Чтение настроек из файла %s.' %fileSettings)
    
 #   jsonString = json.dumps(programSettings)
 #   jsonFile.write(jsonString)
 #   jsonFile.close()
    
    jsonFile = open(fileSettings,'r')
    jsonString = jsonFile.read()    
    programSettings=json.loads(jsonString)
    logging.debug('Настройки из файла %s прочитаны.' %fileSettings)    
except Exception as exc:
    logging.critical('Ошибка открытия файла с настройками %s.\n %s' %(fileSettings, traceback.format_exc()))
    sendReport()
    exit()
else:
    jsonFile.close()
    logging.debug('Файл настроек прочитан и закрыт.')

baseURL = programSettings['baseURL']
baseURLTop = programSettings['baseURLTop']
loglevel = programSettings['loglevel']
destinationPath = programSettings['destinationPath']
regexpBICDB = programSettings['regexpBICDB']
regexpBICUpdate = programSettings['regexpBICUpdate']

logging.info('Загружены следующие настройки:\n'#
             '\turl страницы со справочниками: %s\n'#
             '\turl сайта Банка России: %s\n'#
             '\tуровень логирования: %s\n'#
             '\tкаталог для сохранения файлов: %s\n'#
             '\tрегулярное выражение для справочника: %s\n'#
             '\tрегулярное выражение для корректуры: %s.' %(baseURL,baseURLTop,loglevel,destinationPath,regexpBICDB,regexpBICUpdate) )
try:
    logging.getLogger().setLevel(loglevel)
except Exception as esc:
    logging.warning('Ошибка при изменении уровня протоколирования. \n %s' %traceback.format_exc())
else:
    logging.info('Успешно изменен уровень протоколирования.')

#Заменить в параметрах выражение <date> на сегодняшнюю дату
regexpTmp = re.compile(r'<date>')
regexpBICDB = regexpTmp.sub(currentDate, regexpBICDB)
logging.debug('Регулярное выражение для поиска справочника: %s.' %regexpBICDB)
regexpBICUpdate = regexpTmp.sub(currentDate, regexpBICUpdate)
logging.debug('Регулярное выражение для поиска корректуры: %s.' %regexpBICUpdate)
destinationPath = regexpTmp.sub(currentDate, destinationPath)
logging.debug('Итоговый каталог для сохранения файлов: %s.' %destinationPath)

#TODO: поключиться к странице Банка Росии
try:
    res=requests.get(baseURL)
    res.raise_for_status()
except Exception as esc:
    logging.critical('Ошибка при подключении к ресурсу ЦБ РФ. Приложение остановлено. \n %s' %traceback.format_exc())
    sendReport()
    exit()
else:
    logging.info(res.status_code)

#TODO: получить ссылки на файлы
pageCBR = bs4.BeautifulSoup(res.text, "lxml")
links=pageCBR.select('a')
logging.info('Получено %s ссылок.' % str(len(links)))

# TODO: обработать полученные ссылки при помощи регулярных выражений
#    справочник БИК имеет в имени файла последовательность bik_db_<date>
#    корректура справочника БИК имеет в имени файла последовательность bic_dc_<Номер корректуры>_<date>

linkDownload=[]

regBICDB = re.compile(regexpBICDB)
for link in links:
    BICDB = regBICDB.search(str(link))
    if BICDB != None:
        linkDownload.append(BICDB.group())
        logging.info('Ссылка на справочник: %s.' %BICDB.group())
        break


regBICUpdate = re.compile(regexpBICUpdate)
for link in links:
    BICUpdate = regBICUpdate.search(str(link))
    if BICUpdate != None:
        linkDownload.append(BICUpdate.group())
        logging.info('Ссылка на корректуру: %s.' %BICUpdate.group())
        break

#TODO: сохранение файлов в каталог назначения
#проверяем есть ли такой каталог, если нет, то создаем
if not os.path.exists(destinationPath):
    os.makedirs(destinationPath)
    logging.info('Создан каталог %s.' %destinationPath)
    
for link in linkDownload:
    try:
        fileDownload=requests.get(baseURLTop+link)
        fileDownload.raise_for_status()
    except Exception as esc:
        logging.critical('Ошибка при скачивании файла %s.\n%s' %(baseURLTop+link, traceback.format_exc()))
        break
    else:
        logging.info(fileDownload.status_code)
        
    try:
        destinationFile = open(destinationPath+link.split('/')[-1],'wb')
    except Exception as exc:
        logging.critical('Ошибка сохранения файла %s./n%s' %(destinationPath+link.split('/')[-1],traceback.format_exc()))
    else:
        for chunk in fileDownload.iter_content(100000):
            destinationFile.write(chunk)
        
        destinationFile.close()
        logging.info('Файл %s успешно сохранен.' %(destinationPath+link.split('/')[-1]))

logging.info('Конец работы программы.')
sendReport()