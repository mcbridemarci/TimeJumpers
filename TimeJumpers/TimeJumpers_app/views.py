from django.shortcuts import render
from django.http import HttpResponse
import io, requests, json
#dbWords = {};

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

def query_transcript(transcriptID: str, auth: str):
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
    #print("query_transcript response:", response.json());
    #print("dbWords:", dbWords);
    return dbWords;
    
def findAll(keyword: str, dbWords: list[dict]) -> list[int]:
    r = [];
    #print("dbWords in findAll:", dbWords);
    #print("finding '" + keyword + "'");
    for d in dbWords:
        #print("d['text']:", d['text']);
        if d['text'].lower().find(keyword) >= 0:
            r.append(d['start']);
    return r;

# Create your views here.
def index(request):
    
    #strHTML = "<form action='timeJump/' method='POST'>Enter word to find:</br><input id='searchWord'><input type='submit' value='OK'></form>";

    return render(request, 'index.html');
    
def timeJump(request):
    #for key, value in request.POST.items():
    #    print('Key: %s' % (key) )
    #    print('Value %s' % (value) )
        
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
    #print("strHTML:", strHTML);
    
    return HttpResponse(strHTML);
    
    #transcribe_gcs_with_word_time_offsets("file:///Users/vdo/Desktop/lectureIntro.mov"); #"invalid GCS path"
    #transcribe_gcs_with_word_time_offsets("/Users/vdo/Desktop/lectureIntro.mov");
    #transcribe_gcs_with_word_time_offsets("gs://49783_input/LectureIntrd.mp4"); #fileNotFound error
    #transcribe_gcs_with_word_time_offsets("gs://49783_input/LectureIntro.mp4"); #empty output
    #transcribe_gcs_with_word_time_offsets("gs://49783_input/enunciate.mp4"); #empty output
    #transcribe_gcs_with_word_time_offsets("gs://49783_input/audiu.raw"); #404 No such object - so, at least the above lines are finding the input!
    #transcribe_assemblyai();
