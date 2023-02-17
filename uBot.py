import logging,os,sqlite3,py7zr,random
from urllib.parse import urlparse, parse_qs
from vkbottle import Callback, GroupEventType, GroupTypes, Keyboard, ShowSnackbarEvent,DocMessagesUploader 
from vkbottle.bot import Bot, Message
from pytube import YouTube

admins=[548551718]

bot = Bot("ТОКЕН")
doc_uploader = DocMessagesUploader(bot.api)

async def isadmin(message):
    try:
        user = await bot.api.users.get(message.from_id)
        user=user[0]
        if(user!=None and user.id in admins):
            return True
    except Exception as e:
        print(e)
        return False
    return False

def getdbcon():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection

def getvids(q=""):
    with getdbcon() as con:
        cursor = con.cursor()
        if(q==""):
            sqlite_select_query = "SELECT * FROM `videos`"
            cursor.execute(sqlite_select_query)
        else:
            sqlite_select_query = "SELECT * FROM `videos` WHERE `title` LIKE ?"
            cursor.execute(sqlite_select_query,[q])
        return cursor.fetchall()

def addvid(vid):
    with getdbcon() as con:
        cursor = con.cursor()
        sqlite_select_query = "INSERT INTO `videos` (`id`,`title`,`author`,`file`) VALUES (?,?,?,?)"
        yt = YouTube(f"https://www.youtube.com/watch?v={vid}")
        print(yt.streams)
        if(len(yt.streams)>=1):
            stream = yt.streams[1]
        else:
            stream = yt.streams[0]
        stream.download('./vids')
        cursor.execute(sqlite_select_query,[vid,yt.title,yt.author,stream.default_filename])
        return True

def isvid(vid):
    with getdbcon() as con:
        cursor = con.cursor()
        sqlite_select_query = "SELECT * FROM `videos` where `id` = ?"
        cursor.execute(sqlite_select_query,[vid])
        return cursor.fetchall()!=[]

def getvid(vid):
    with getdbcon() as con:
        cursor = con.cursor()
        sqlite_select_query = "SELECT * FROM `videos` where `id` = ?"
        cursor.execute(sqlite_select_query,[vid])
        return cursor.fetchone()

@bot.on.private_message()
async def send_callback_button(message: Message):
    if not os.path.exists("vids"):
        os.mkdir("vids")
    try:
        if(message.text):
            if(message.text=="/start"):
                await message.answer("Привет \n/start - Привет\n/vids - Видосики\n/dlvid (айди) - Скачать видосик\n/upvid (айди) - Залить видео\n/search (название видео) - Поиск по видео\n/getuid - Получить UID")
            elif message.text=="/vids":
                txt="Видосики:\n"
                if(getvids()==[]):
                    txt+="Нету"
                for vid in getvids():
                    txt+=f"\"{vid['title']}\" ({vid['author']}); {vid['id']}\n"
                await message.answer(txt)
            elif message.text.startswith("/dlvid"):
                if(len(message.text.split())==2):
                    vid={'v':message.text.split()[1]}
                    if not isvid(vid['v']):
                        await message.answer("Видосик не найден")
                    else:
                        await message.answer("Видосик заливается, подождите")
                        doc=await doc_uploader.upload(file_source=f"./vids/{getvid(vid['v'])['file']}",peer_id=message.peer_id,title=getvid(vid['v'])['file'])
                        await message.answer(f"Видео {getvid(vid['v'])['title']} успешно загружено!",attachment=doc)
                else:
                    await message.answer("Требуется аргумент")
            elif message.text.startswith("/upvid"):
                if(len(message.text.split())==2):
                    vid=parse_qs(urlparse(message.text.split()[1]).query)
                    if('v' in vid):
                        vid['v']=vid['v'][0]
                        if isvid(vid['v']):
                            await message.answer("Видосик уже существует")
                        else:
                            #/dlvid https://www.youtube.com/watch?v=dQw4w9WgXcQ
                            await message.answer("Видосик заливается, подождите")
                            addvid(vid['v'])
                            await message.answer(f"Видео {getvid(vid['v'])['title']} готово!")
                    else:
                        await message.answer("Неверный URL")
                else:
                    await message.answer("Требуется аргумент")
            elif message.text.startswith("/search"):
                q=message.text.replace("/search ","")
                if(q=="" or q=="/search"):
                    await message.answer("Требуется аргумент")
                else:
                    txt="Видосики:\n"
                    if(getvids(q)==[]):
                        txt+="Нету"
                    for vid in getvids(q):
                        txt+=f"\"{vid['title']}\" ({vid['author']}); {vid['id']}\n"
                    await message.answer(txt)
            elif message.text.startswith("/getlnk"):
                vid=message.text.replace("/getlnk ","")
                if(vid=="" or vid=="/getlnk"):
                    await message.answer("Требуется аргумент")
                    return 0 
                await message.answer(f"https://youtube.com/watch?v={vid}")    
            elif message.text.startswith("/getuid"):
                try:
                    uid=await bot.api.users.get(message.from_id)
                    uid=uid[0].id
                    await message.answer(f"Ваш UID: {uid}")
                except Exception as e:
                    print("e!!",e,"!!e")
                    await message.answer(f"Произошла ошибка при получении UID.")
            elif message.text.startswith("/getvids"):
                isadminn= await isadmin(message)
                if(isadminn):
                    await message.answer("Сжатие и загрузка. Пожалуйста, подождите.")
                    if os.path.exists("videos.7z"):
                        os.remove("videos.7z")
                    pwd=random.randbytes(6).hex()
                    with py7zr.SevenZipFile('videos.7z', 'w',password=pwd) as archive:
                        archive.writeall('./vids', 'vids')
                        archive.writeall('./database.db', 'database.db')
                    await message.answer("Сжатие успешно. Загружаю..")
                    doc=await doc_uploader.upload(file_source=f"./videos.7z",peer_id=message.peer_id,title="videos.7z")
                    await message.answer(f"Библиотека видеороликов успешно загружена! Пароль: {pwd}",attachment=doc)
    except Exception as e:
        print("e!!",e,"!!e")
        await message.answer(f"Произошла ошибка.")
bot.run_forever()