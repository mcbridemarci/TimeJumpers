from django.shortcuts import render;
from django.http import HttpResponse;
from TimeJumpers_app.models import User, Video;
from hmac import compare_digest #testing...
import io, requests, json, math, random, hashlib;

#from dajaxice.utils import deserialize_form;
##from myapp.form import DreamrealForm;
#from dajax.core import Dajax;
##from myapp.models import Dreamreal;

currentAudio = "";
dbWordToTimes = {};

def local_hash(password: str):
    hashery = hashlib.sha256()
    hashery.update(bytes(password, 'utf-8'));
    return hashery.digest();

def login(request):
    context = {};
    if "email" not in request.POST: #render login page
        context["title"] = "Login";
    else: #input sent
        context["title"] = "Login";
        
        #get email and hash password
        email = request.POST.get("email");
        pwHash = local_hash(request.POST.get("password"));
        
        #if creating a new user
        if request.POST.get("action")=="create":
            p = User(email=email, password=pwHash);
            p.save();
        else: #opening an existing account
            currUser = User.objects.get(email=email);
            if currUser and str(pwHash) == currUser.password: #compare_digest(currUser.password, pwHash):
                context["userID"] = currUser.id;
                return specify(request, currUser.id); #TODO: redirect such that the URL is not "/login"
            else:
                context["error"] = "The credentials provided could not be verified. Try again.";
            
    return render(request, 'login.html', context);
    

#POC: test jumping to a random point in the video
def testTimeJump(request):
    #http://127.0.0.1:8000/testTimeJump/?time=4
    audio_url = "https://storage.googleapis.com/49783_input/LectureIntro.mp4";
    time = request.GET.get("time");
    time = int(time) if time else random.randint(0,4);
    
    #video position "currentTime" is in seconds (while findAll returns milliseconds)
    strHTML = """<video id="vid1" width="750" height="563" controls="controls" autoplay="autoplay">
                <source src="{}" type="video/mp4">
                <object data="" width="1500" height="1125">
                <embed width="1500" height="1125" src="{}">
                </object>
                </video>
                <script>
                    document.getElementById('vid1').currentTime = {};
                </script>""".format(audio_url, audio_url, time);
                
    return HttpResponse(strHTML);

#POC: test writing to the database
def testDBWrite(request):
    p = Video(location="https://storage.googleapis.com/49783_input/LectureIntro.mp4", transcriptID="jilog6fau-2d87-4ad4-a8d3-fd795ee4d06f");
    p.save();
    return render(request, 'home.html');
    
#retrieve new transcription of specified audio file
def transcribe_assemblyai(auth: str, audio_url: str): #9 dollars to process 10 hours of input
    endpoint = "https://api.assemblyai.com/v2/transcript";
    
    #json = {
    #  "audio_url": "https://s3-us-west-2.amazonaws.com/blog.assemblyai.com/audio/8-7-2018-post/7510.mp3"
    #}
    
    json = {
      "audio_url": audio_url
      };
    
    headers = {
        "authorization": auth,
        "content-type": "application/json"
    };
    
    response = requests.post(endpoint, json=json, headers=headers);
    
    return response.json();
    
#retrieve existing transcript
def query_transcript(transcriptID: str, auth: str) -> dict:
    #sometimes returns OSError: [Errno 41] Protocol wrong type for socket
    #   in such cases, retry
    dbWords = None;
    endpoint = "https://api.assemblyai.com/v2/transcript/" + transcriptID;
    headers = {
        "authorization": auth,
    };
    import datetime, time;
    while not dbWords:
        response = requests.get(endpoint, headers=headers);
        
        #return response.json();
        dbWords = response.json();
        if not dbWords:
            time.sleep(5);
        else:
            #print(dbWords);
            dbWords = dbWords['words'];
    
    return dbWords;
    
#can be searched even for partial matches!
def map_word_to_times(dbWords: list[dict], context: int) -> dict:
    #dbWords: list of dictionaries like "{'text': 'Hello,', 'confidence': 0.96, 'end': 600, 'start': 0}"
    #r: list of dictionaries like "{'hello': [[0, 'Hello everyone how']]}"
    r = {};
    for i in range(0, len(dbWords)):
        key = ''.join(filter(str.isalnum, dbWords[i]['text'])).lower();
        if key not in r:
            r[key] = [];
        r[key].append([dbWords[i]['start'], " ".join([("{}" if j!=i else "<strong>{}</strong>").format(dbWords[j]['text']) for j in range(max(0,i-context),min(i+context+1,len(dbWords)))])]);
    return r;
    
#scan trancript for given keyword; return times where found, and surrounding words for context
def findAll(searchword: str, dbWordToTimes: dict) -> list[int]:
    r = [];
    searchword = searchword.lower();
    for key in dbWordToTimes.keys():
        if key.find(searchword) >= 0:
            #append time and context of occurrence
            r += dbWordToTimes[key];
            
    return r;

#landing page
def index(request):
    return render(request, 'index.html');

#specify video to use
def specify(request, userID=0):
    context = { };
    context["userID"] = userID;
    if userID != 0:
        context ["existing_videos"] = Video.objects.filter(userID=userID);
     #context ["existing_videos"] = Video.objects.all();
    return render(request, 'specify_video.html', context);
    
#pad strIn with as many copies of strPad as is required to reach a length of iLen
def pad(strIn: str, strPad: str, iLen: int) -> str:
    return "".join([strPad]*(iLen-len(strIn))) + strIn;

#prepare links for search results
def convertTimesToLinks(pos: list) -> None:
    for i in range(0, len(pos)):
        #to enable navigation, use the second line from here:
        #pos[i] = "<a href='.'>" + convertTimeToHuman(pos[i][0]) + "</a>: '... " + pos[i][1] + " ...'";
        pos[i] = "<a href='javascript:setVideoTime(" + str(float(pos[i][0])/float(1000)) + ")'>" + convertTimeToHuman(pos[i][0]) + "</a>: '... " + pos[i][1] + " ...'";

#convert time from milliseconds to human-readable (HH:MM:SS)
def convertTimeToHuman(iTimeMs: int) -> str:
    return str(math.floor(iTimeMs/3600000)) + ":" + pad(str(math.floor((iTimeMs%3600000)/60000)), "0", 2) + ":" + pad(str(math.floor((iTimeMs%60000)/1000)), "0", 2);

#POC: analyzing a video stored locally
def read_file(input, chunk_size=5242880):
    with input as _file:
        while True:
            data = _file.read(chunk_size)
            if not data:
                break
            yield data

#POC: analyzing a video stored locally
def testLocalVideo(request):
    audio_local = '/Users/vdo/Documents/Jeffrey/CMU/Courses/2021T2/49783/project/testData/LectureIntro.mp4';
    auth = getAuth();
    headers = {'authorization': auth};
    response = requests.post('https://api.assemblyai.com/v2/upload',
                         headers=headers,
                         data=read_file(audio_local));
    print(response.json()); #{'upload_url': 'https://cdn.assemblyai.com/upload/d81401ab-87c6-4d4d-a22f-b8a664aa3f8c'}
    return render(request, 'playLocalVideo.html', {'json': response.json()});
    
def getAuth():
    return "9ce7bcff260346dcb2810fa76023732b"; #Jeffrey's personal account; 5 hr/month limit

def upload_assemblyai(input):
    auth = getAuth();
    print("uploading...");
    headers = {'authorization': auth};
    response = requests.post('https://api.assemblyai.com/v2/upload',
                         headers=headers,
                         data=read_file(input));
    return response.json();
    
#search page
def query_video(request):
    
    global dbWordToTimes;
    context = {}; #container to send data to the view
    audio_location = "";
    userID = request.POST.get("userID", None) if "userID" in request.POST else 0;
    
    if "searchWord" in request.POST: #no need to query transcription as we already have it in memory
        searchWord = request.POST.get("searchWord", None).lower();
        audio_location = request.POST.get("videoURL", None);
        
        #find all instances of searchWord
        pos = findAll(searchWord, dbWordToTimes);
        convertTimesToLinks(pos);
        
        context ["searchWord"] = searchWord;
        context ["results"] = pos;
        
    else: #generate a transcript and keep it for later
        auth = getAuth();
        
        transcriptID = request.POST.get("existing", None);
        if transcriptID: #user selected saved transcript
            audio_location = Video.objects.get(transcriptID = transcriptID).location;
        else: #proceed as if this is a new video
            audio_location = request.POST.get("videoLocation", None);
            audio_url = "";
            #if video not hosted at a public URL
            if not audio_location: #put it somewhere that AssemblyAI can find it
                context ["isOnline"] = 0;
                audio_location = request.POST.get("localfile", None);
                audio_url = upload_assemblyai(request.FILES["localfile"]); #upload to AssemblyAI
                audio_location = request.FILES["localfile"]; #<class 'django.core.files.uploadedfile.InMemoryUploadedFile'>
                #context["videoContent"] = audio_location #still <class 'django.core.files.uploadedfile.InMemoryUploadedFile'>
                #print('type(context["videoContent"]): ', type(context["videoContent"]));
                audio_location = audio_location.temporary_file_path;
                #print("audio_location.temporary_file_path:", audio_location.temporary_file_path);
            else:
                audio_url = audio_location;
            
            #request production of a transcript
            transcriptID = transcribe_assemblyai(auth, audio_url)['id'];
            
            #save video's original location, plus its transcript
            p = Video(location=audio_location, transcriptID=transcriptID, userID=userID);
            p.save();
        
        dbWords = query_transcript(transcriptID, auth); #list of dictionaries; one per word
        #print(dbWords);
        dbWordToTimes = map_word_to_times(dbWords, 2);
                
    context["videoURL"] = audio_location;
    context["userID"] = userID;
        
    return render(request, 'play.html', context);
    #return render(request, 'query_video.html', context);

def query_local(request):
    #test = ;
    #testList = test.split("text");
    
    #for item in testList:
    #    if item.count('"')!=10:
    #        print(item);
    
    #for i in range(1, len(test)-1):
    #    if test[i]=='"' and test[i-1].isalnum() and test[i+1].isalnum():
    #        print(test[i-10:i+10]);
    
    #audio_local = '/Users/vdo/Documents/Jeffrey/CMU/Courses/2021T2/49783/project/testData/LectureIntro.mp4';
    #auth = "9ce7bcff260346dcb2810fa76023732b";
    #headers = {'authorization': auth};
    #response = requests.post('https://api.assemblyai.com/v2/upload',
    #                     headers=headers,
    #                     data=read_file(audio_local));
    #print(response.json()); #{'upload_url': 'https://cdn.assemblyai.com/upload/d81401ab-87c6-4d4d-a22f-b8a664aa3f8c'}
    #return render(request, 'query_local.html');
    return render(request, 'query_local.html');

#@dajaxice_register
def getJSONTranscripts(request):
    return "test";
