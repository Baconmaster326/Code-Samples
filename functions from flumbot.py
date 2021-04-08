
# Function for taking user clips to download and add to community soundclips for bot
# takes input msg, usually "[command name] mp3 [youtube url]"

msg.remove('mp3')                   #get only the youtube url from argument
msg = str(msg)
char_list = ["'", "[", "]", ","]
for i in char_list:
    y = y.replace(i, '')
link = str(y)

ydl_opts = {                        # call youtube-dl to download only the audio
    'format': 'bestaudio/best',
    'postprocessors': [{
    'key': 'FFmpegExtractAudio',
    'preferredcodec': 'mp3',
    'preferredquality': '192',
    }],
    }
with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([link])
        
for file in os.listdir('./'):       # place clip in proper folder for community uploads
    if file.endswith(".mp3"):
        location = os.path.join("./", file)
shutil.move(location, './Clips/usersub')
                                    # report succesful addition of clip
msg = "Successfully added <" + link + "> to user submissions folder"
await ctx.send(msg)


# Next function is for passing mp3s or wavs to be played in Discord voice
# cliplocation is the filepath to the clip, ctx and client are discord sockets, and overide is for duration hardcoding

async def playclip(cliplocation, ctx, client, overide):
    try:
        channel = ctx.message.author.voice.channel          #is user in a channel?
    except AttributeError:
        msg = "You don't appear to be in a channel"
        await ctx.send(msg)
        return False
    print('starting to play clip')
    duration = librosa.get_duration(filename=cliplocation) + 1   # get duration of clip to play from librosa
    if (overide != 0):
        duration = overide
    channel = ctx.message.author.voice.channel                  # join the voice channel of the author of the message
    voice = get(client.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        await voice.move_to(channel)
    else:
        voice = await channel.connect()
    source = FFmpegPCMAudio(cliplocation)                       # create FFmpeg instance on host, and cast to discord socket
    source = discord.PCMVolumeTransformer(source)
    source.volume = 1.5
    player = voice.play(source)
    await asyncio.sleep(duration)                               # wait for clip to finish, then close connection and leave
    player = voice.stop()
    await ctx.voice_client.disconnect()
    print('done playing clip')
    return


# Next function is a game which takes a midi, converts to a wav file to play over discord voice, lets users vote on what they thought the song was
# reference here >>> https://cdn.discordapp.com/attachments/549996148643856389/829793672308326470/unknown.png

async def midimania(ctx, client):
    for file in os.listdir("./"):                                   # find all midi files, remove any leftovers wav files
        if file.endswith(".wav"):
            os.remove(file)
    msg = await ctx.send("Please wait while I prepare your midi :)", tts=True)
    midifiles = []
    filenames = []
    for dirpath, subdirs, files in os.walk('./Music/MIDI'):
        for x in files:
            if x.endswith(".mid"):
                filenames.append(x)
                midifiles.append(os.path.join(dirpath, x))
    cliplocation = random.choice(midifiles)
    miditoaudio.to_audio('./Music/OPL2.sf2', cliplocation, './', out_type='wav')    # call helper function to call fluidsynth with given soundfont and clip
    person = os.path.split(cliplocation)
    person = person[1]
    print(person)
    place = str(person[:-4]) + '.wav'
    await msg.delete()
    msg = "It's time to guess that Midi!\nYou'll have 30 seconds to pick the correct song from 4 choices\nPICK ONLY ONE TIME"
    await ctx.send(msg, tts=True)
    await asyncio.sleep(10)         
    await playclip(place, ctx, client, 30)                                  #play clip for 30 seconds
    await asyncio.sleep(3)
    os.remove(place)                                                        #remove wav file we just played
    select = random.randint(1, 4)
    A, B, C, D = ' ', ' ', ' ', ' '                                         #initialize answer choices, not sure if nessisary
    samples = random.sample(os.listdir('./Music/MIDI/'), 4)                 #get random selection of midis from folder
    A, B, C, D = samples[0], samples[1], samples[2], samples[3]
    while (A == person or B == person or C == person or D == person):       #keep getting random samples until every answer is unique, select is the index for the correct answer
        print("repetition detected")
        samples = random.sample(os.listdir('./Music/MIDI/'), 4)
        A, B, C, D = samples[0], samples[1], samples[2], samples[3]
    if (select == 1):
        A = str(person)
        answer = '\U0001F1E6'
        printable = ':regional_indicator_a:'
    if (select == 2):
        B = str(person)
        answer = '\U0001F1E7'
        printable = ':regional_indicator_b:'
    if (select == 3):
        C = str(person)
        answer = '\U0001F1E8'
        printable = ':regional_indicator_c:'
    if (select == 4):
        D = str(person)
        answer = '\U0001F1E9'
        printable = ':regional_indicator_d:'

    #could add formatted string here
    msg = "Was it\n:regional_indicator_a:\t\u21e6\t" + A[:-4] +
    "\n:regional_indicator_b:\t\u21e6\t" + B[:-4] + "\n:regional_indicator_c:\t\u21e6\t" + C[:-4] + "\n:regional_indicator_d:\t\u21e6\t" + D[:-4]
    
    message = await ctx.send(msg)
    await message.add_reaction('\U0001F1E6')
    await message.add_reaction('\U0001F1E7')
    await message.add_reaction('\U0001F1E8')
    await message.add_reaction('\U0001F1E9')
    return answer, printable                        #answer is the unicode emoji, and printable is the non unicode emoji, makes formatting the winner list simpler, which is called 30 seconds after this


# Function to award points, display winners, from midimania and geddit
# winners is a list of people who correctly answered the game and mod is a modifer for how many points to award

async def winnerlist(ctx, client, winners, printable, mod):
    filename = './bin/en_data/userdata.json'
    with open(filename, "r") as file:
        data = json.load(file)
    msg = "The correct answer was " + printable + "\n\nCongratulations to:\n"
    await ctx.send(msg, tts=True)
    if len(winners) == 0:                       # if nobody answered correctly, congrats to flumbot
        data['Flumbot#1927']['score'] = data['Flumbot#1927']['score'] + mod   # increase the score
        await ctx.channel.send(file=discord.File('./Pics/flumbus.png')) # pre canned picture to save resources
        msg = "Better luck next time folks! Flumbot has won, he has " + str(data['Flumbot#1927']['score']) + " marcs!"
        await ctx.send(msg)
        with open(filename, "w") as file:
            json.dump(data, file)
        return
    for x in winners:                           # for each person in winners list
        try:
            data[x]['score'] = data[x]['score'] + mod # do they have a wallet / entry in hash table? if so give them credit for winning
        except KeyError:
            try:
                data[x] = data[x]               #give them one and give them credit for winning
                data[x]['score'] = mod
            except KeyError:
                data[x] = {}
                data[x]['score'] = mod
                
        im = Image.open("./Pics/blank.png")     # use pillow to graph their username with random color and certain font
        d = ImageDraw.Draw(im)
        location = (0, 10)
        text_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        d.text(location, x[:-5], font=ImageFont.truetype(font='./Pics/sponge.ttf', size=56), fill=text_color)
        im.save("person.png")
        await ctx.channel.send(file=discord.File('person.png')) # send the picture
        os.remove('person.png')                                 # remove from host
        msg = x[:-5] + " has " + str(data[x]['score']) + " marcs!" # send their score to display
        await ctx.send(msg)
    with open(filename, "w") as file:                           # at end write the file
        json.dump(data, file)
    msg = "\n:clap::clap::clap::clap::clap::clap:\n"
    await ctx.send(msg, tts=True)

# Next game takes 4 random images from top 300 images of any subreddit from reddit, gives you the title, and you must guess the image
# reference here >>> https://cdn.discordapp.com/attachments/549996148643856389/829793221524848660/unknown.png

async def gedditdx(ctx, client, args):
    reddit = praw.Reddit(client_id='id',                    # create praw instance with credentials
                         client_secret='secret',
                         username='user',
                         password='pass',
                         user_agent='flumbot')
    id = []
    pics = []                                               # start arrays for links
    sr = reddit.subreddit(args).hot(limit=300)
    for submission in sr:                                   # grab 300 images, without id repeats
        if not submission.is_self:
            if submission.url.endswith('.jpg') or submission.url.endswith('.png'):
                id.append(submission.id)
                pics.append(submission.url)
    if len(pics) < 4:                                       # if we can get 4 pictures return an error
        print('user posted a text only subreddit, let him know the news')
        msg = "Your subreddit doesn't appear to have enough pictures I can use, please use a different one."
        await ctx.send(msg)
        return False
    post = reddit.submission(id=random.choice(id))          # grab random post from list
    while len(post.title) > 256:
        post = reddit.submission(id=random.choice(id))
    person = post.url
    msg = "It's time to for GEDDITDX!\nYou'll have 30 seconds to determine what picture matches the title that came " \
          "from r/" + post.subreddit.display_name + "\nPICK ONLY ONE TIME!!!"
    if args == 'all':                                       # r/all is a weird one treat it differently
        msg = "It's time to for GEDDITDX!\nYou'll have 30 seconds to determine what picture matches the title that " \
              "came from r/all\nPICK ONLY ONE TIME!!!"
    await ctx.send(msg, tts=True)
    await asyncio.sleep(12)                                 #everything here pretty much repeats midimania in terms of displaying the question
    embed = discord.Embed(title=post.title,
                          colour=discord.Colour.from_rgb(random.randint(0, 255), random.randint(0, 255),
                                                         random.randint(0, 255)))
    samples = random.sample(pics, 4)
    select = random.randint(1, 4)
    A, B, C, D = samples[0], samples[1], samples[2], samples[3]
    while A == person or B == person or C == person or D == person:
        print("repetition detected")
        samples = random.sample(pics, 4)
        A, B, C, D = samples[0], samples[1], samples[2], samples[3]
    if select == 1:
        A = str(person)
        answer = '\U0001F1E6'
        printable = ':regional_indicator_a:'
    if select == 2:
        B = str(person)
        answer = '\U0001F1E7'
        printable = ':regional_indicator_b:'
    if select == 3:
        C = str(person)
        answer = '\U0001F1E8'
        printable = ':regional_indicator_c:'
    if select == 4:
        D = str(person)
        answer = '\U0001F1E9'
        printable = ':regional_indicator_d:'
    answers = [A, B, C, D]
    await ctx.send(embed=embed)
    await getpicture(answers)                               # refer to next function, this collages the 4 posts into one image and places the answer choices on top
    message = await ctx.channel.send(file=discord.File('person.jpg'))   # send to channel and remove from host machine
    for file in os.listdir("./"):
        if file.endswith(".jpg"):
            os.remove(file)
    await message.add_reaction('\U0001F1E6')
    await message.add_reaction('\U0001F1E7')
    await message.add_reaction('\U0001F1E8')
    await message.add_reaction('\U0001F1E9')
    return answer, printable

# Helper function to Gedditdx, collages 4 reddit image links into content for gedditdx
# see above reference for sample output

async def getpicture(links):
    x = 0
    for image in links:             # download the image data, increment their filenames
        print(image)
        img_data = requests.get(image).content
        with open('image'+str(x)+'.jpg', 'wb') as handler:
            handler.write(img_data)
        x += 1
    im1 = Image.open('./image0.jpg')
    im2 = Image.open('./image1.jpg')
    im3 = Image.open('./image2.jpg')
    im4 = Image.open('./image3.jpg')

    # all helper functions to collage the pictures in a plesant looking form, not needed in functions but I thought I would have to call multiple times
    
    def get_concat_h_multi_resize(im_list, resample=Image.BICUBIC):
        min_height = min(im.height for im in im_list)
        im_list_resize = [im.resize((int(im.width * min_height / im.height), min_height), resample=resample)
                          for im in im_list]
        total_width = sum(im.width for im in im_list_resize)
        dst = Image.new('RGB', (total_width, min_height))
        pos_x = 0
        for im in im_list_resize:
            dst.paste(im, (pos_x, 0))
            pos_x += im.width
        return dst

    def get_concat_v_multi_resize(im_list, resample=Image.BICUBIC):
        min_width = min(im.width for im in im_list)
        im_list_resize = [im.resize((min_width, int(im.height * min_width / im.width)), resample=resample)
                          for im in im_list]
        total_height = sum(im.height for im in im_list_resize)
        dst = Image.new('RGB', (min_width, total_height))
        pos_y = 0
        for im in im_list_resize:
            dst.paste(im, (0, pos_y))
            pos_y += im.height
        return dst

    def get_concat_tile_resize(im_list_2d, resample=Image.BICUBIC):
        im_list_v = [get_concat_h_multi_resize(im_list_h, resample=resample) for im_list_h in im_list_2d]
        return get_concat_v_multi_resize(im_list_v, resample=resample)

    # collage all images
    get_concat_tile_resize([[im1, im2],
                            [im3, im4]]).save('./image4.jpg')

    # image4 is the collaged image, get ready to write font on it
    im = Image.open("./image4.jpg")
    d = ImageDraw.Draw(im)
    letters = ['A', 'B', 'C', 'D']
    fontsize = int(.05*im.width)
    fontwidth = int(im.width*.0075)
    # give each a random color and place on a scale with height and width of collaged image
    for letter in letters:
        text_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        if letter == 'A':
            location = (int(im.width*.02), int(im.height*.02))
        if letter == 'B':
            location = (int(im.width*.92), int(im.height*.02))
        if letter == 'C':
            location = (int(im.width*.02), int(im.height*.92))
        if letter == 'D':
            location = (int(im.width*.92), int(im.height*.92))
        d.text(location, letter, font=ImageFont.truetype(font='./Pics/sponge.ttf', size=fontsize), fill=text_color,
               stroke_width=fontwidth, stroke_fill="#000000")
    # save as a filename gedditdx knows what to do with    
    im.save("person.jpg")
    return True
