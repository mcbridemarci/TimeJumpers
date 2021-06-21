from django.shortcuts import render;
from django.http import HttpResponse;
from TimeJumpers_app.models import Video;
import io, requests, json, math, random;
currentAudio = "";
dbWordToTimes = {};

#POC: playing a video stored locally
def testLocalVideo(request):
    return render(request, 'playLocalVideo.html');

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
    while not dbWords:
        response = requests.get(endpoint, headers=headers);
        
        #return response.json();
        dbWords = response.json()['words'];
    
    return dbWords;
    
#does not work for partial matches - I cannot anticipate every last keyword the crazy use might search!
def map_word_to_times(dbWords: list[dict], context: int) -> dict:
    #dbWords: list of dictionaries like "{'text': 'Hello,', 'confidence': 0.96, 'end': 600, 'start': 0}"
    #r: list of dictionaries like "{'hello': [[0, 'Hello everyone how']]}"
    r = {};
    for i in range(0, len(dbWords)):
        key = ''.join(filter(str.isalnum, dbWords[i]['text'])).lower();
        if key not in r:
            r[key] = [];
        r[key].append([dbWords[i]['start'], " ".join([("{}" if j!=i else "<strong>{}</strong>").format(dbWords[j]['text']) for j in range(max(0,i-context),min(i+context+1,len(dbWords)))])]);
        #r[key].append([dbWords[i]['start'], " ".join([dbWords[j]['text'] for j in range(max(0,i-context),min(i+context+1,len(dbWords)))])]);
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

#landing page
def specify(request):
    context = { };
    context ["existing_videos"] = Video.objects.all();
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

#search page
def query_video(request):
    
    global dbWordToTimes;
    context = {}; #container to send data to the view
    audio_url = "";
    
    if "searchWord" in request.POST: #no need to query transcription as we already have it in memory
        searchWord = request.POST.get("searchWord", None).lower();
        audio_url = request.POST.get("videoURL", None);
        
        #find all instances of searchWord
        pos = findAll(searchWord, dbWordToTimes);
        convertTimesToLinks(pos);
        
        context ["searchWord"] = searchWord;
        context ["results"] = pos;
        
    else: #generate a transcript and keep it for later
        auth = "9ce7bcff260346dcb2810fa76023732b"; #Jeffrey's personal account; 5 hr/month limit
        
        if "existing" in request.POST:
            transcriptID = request.POST.get("existing", None);
            audio_url = Video.objects.get(transcriptID = transcriptID).location;
        else: #proceed as if this is a new URL
            audio_url = request.POST.get("videoURL", None);
            transcriptID = transcribe_assemblyai(auth, audio_url)['id'];
            print("Transcript ID:", transcriptID);
            
        dbWords = query_transcript(transcriptID, auth); #list of dictionaries; one per word
        dbWordToTimes = map_word_to_times(dbWords, 2);
        
    context["videoURL"] = audio_url;
        
    return render(request, 'query_video.html', context);
