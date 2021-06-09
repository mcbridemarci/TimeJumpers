from django.shortcuts import render
from django.http import HttpResponse
import io, requests, json, math;

#retrieve new transcription of specified audio file
def transcribe_assemblyai(auth: str, audio_url: str): #9 dollars to process 10 hours of input
    endpoint = "https://api.assemblyai.com/v2/transcript"
    
    #json = {
    #  "audio_url": "https://s3-us-west-2.amazonaws.com/blog.assemblyai.com/audio/8-7-2018-post/7510.mp3"
    #}
    
    json = {
      "audio_url": audio_url
      }
    
    headers = {
        "authorization": auth,
        "content-type": "application/json"
    }
    
    response = requests.post(endpoint, json=json, headers=headers)
    
    #print("JSON response:", response.json());
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
        key = dbWords[i]['text'].lower();
        if key not in r:
            r[key] = [];
        r[dbWords[i]['text']].append([dbWords[i]['start'], key, " ".join([dbWords[j]['text'] for j in range(max(0,i-context),min(i+context+1,len(dbWords)))])]);
    return r;
    
#scan trancript for given keyword; return times where found, and surrounding words for context
def findAll(keyword: str, dbWords: list[dict], context: int) -> list[int]:
    r = [];
    for i in range(0, len(dbWords)):
        if dbWords[i]['text'].lower().find(keyword) >= 0:
            r.append([dbWords[i]['start'], " ".join([("{}" if j!=i else "<strong>{}</strong>").format(dbWords[j]['text']) for j in range(max(0,i-context),min(i+context+1,len(dbWords)))])]);
    return r;

#landing page
def index(request):
    return render(request, 'index.html');

#pad strIn with as many copies of strPad as is required to reach a length of iLen
def pad(strIn: str, strPad: str, iLen: int) -> str:
    return "".join([strPad]*(iLen-len(strIn))) + strIn;

#prepare links for search results
def convertTimesToLinks(pos: list) -> None:
    for i in range(0, len(pos)):
        #pos[i] = "<a href='.'>" + convertTimeToHuman(pos[i][0]) + "</a>: '... " + pos[i][1] + " ...'";
        pos[i] = "<a href='javascript:setVideoTime(" + str(float(pos[i][0])/float(1000)) + ")'>" + convertTimeToHuman(pos[i][0]) + "</a>: '... " + pos[i][1] + " ...'";

#convert time from milliseconds to human-readable (HH:MM:SS)
def convertTimeToHuman(iTimeMs: int) -> str:
    return str(math.floor(iTimeMs/3600000)) + ":" + pad(str(math.floor((iTimeMs%3600000)/60000)), "0", 2) + ":" + pad(str(math.floor((iTimeMs%60000)/1000)), "0", 2);
    
#search page
def query_video(request):
    
    audio_url = "https://storage.googleapis.com/49783_input/LectureIntro.mp4";
    context = { "videoURL": audio_url };
    
    if "searchWord" in request.POST:
        searchWord = request.POST.get("searchWord", None).lower();
        boolTestTranscription = False;
        auth = "9ce7bcff260346dcb2810fa76023732b"; #Jeffrey's personal account; 5 hr/month limit
        
        transcriptID = "jilog6fau-2d87-4ad4-a8d3-fd795ee4d06f"; #LectureIntro.mp4
        
        #if boolTestTranscription, make call to 'transcribe_assemblyai'
        if boolTestTranscription:
            transcriptID = transcribe_assemblyai(auth, audio_url)['id'];
        #else: #reuse existing transcript
        
        dbWords = query_transcript(transcriptID, auth); #list of dictionaries; one per word
        
        #find all instances of searchWord
        pos = findAll(searchWord, dbWords, 2);
        convertTimesToLinks(pos);
        
        context ["searchWord"] = searchWord;
        context ["results"] = pos;
        
    #return HttpResponse("Where can I upload, eh?<br>");
    
    return render(request, 'query_video.html', context);
    
#display video queued to desired time
def query_videoV1(request):
    
    searchWord = request.POST.get("searchWord", None).lower();
    boolTestTranscription = False;
    auth = "9ce7bcff260346dcb2810fa76023732b"; #Jeffrey's personal account; 5 hr/month limit
    audio_url = "https://storage.googleapis.com/49783_input/LectureIntro.mp4";
    
    transcriptID = "jilog6fau-2d87-4ad4-a8d3-fd795ee4d06f"; #LectureIntro.mp4
    
    #if not boolTestTranscription, skip call to 'transcribe_assemblyai'
    if boolTestTranscription:
        transcriptID = transcribe_assemblyai(auth, audio_url)['id'];
    dbWords = query_transcript(transcriptID, auth); #list of dictionaries
    
    #return HttpResponse("Where can I upload, eh?<br>");
    pos = findAll(searchWord, dbWords);
    
    #if keyword found
    if pos:
        #video position "currentTime" is in seconds (while findAll returns milliseconds)
        strHTML = """<video id="vid1" width="750" height="563" controls="controls" autoplay="autoplay">
                    <source src="{}" type="video/mp4">
                    <object data="" width="1500" height="1125">
                    <embed width="1500" height="1125" src="{}">
                    </object>
                    </video>
                    <script>
                        document.getElementById('vid1').currentTime = {};
                    </script>""".format(audio_url, audio_url, float(pos[0])/float(1000) if pos else 0);
    else:
        strHTML = "Zero results found for keyword '{}'.".format(searchWord);
    
    return HttpResponse(strHTML);
    
    #transcribe_gcs_with_word_time_offsets("file:///Users/vdo/Desktop/lectureIntro.mov"); #"invalid GCS path"
    #transcribe_gcs_with_word_time_offsets("/Users/vdo/Desktop/lectureIntro.mov");
    #transcribe_gcs_with_word_time_offsets("gs://49783_input/LectureIntrd.mp4"); #fileNotFound error
    #transcribe_gcs_with_word_time_offsets("gs://49783_input/LectureIntro.mp4"); #empty output
    #transcribe_gcs_with_word_time_offsets("gs://49783_input/enunciate.mp4"); #empty output
    #transcribe_gcs_with_word_time_offsets("gs://49783_input/audiu.raw"); #404 No such object - so, at least the above lines are finding the input!
    #transcribe_assemblyai();
