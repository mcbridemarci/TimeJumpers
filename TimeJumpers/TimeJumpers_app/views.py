from django.shortcuts import render
from django.http import HttpResponse

def transcribe_gcs_with_word_time_offsets(gcs_uri):
    """Transcribe the given audio file asynchronously and output the word time
    offsets."""
    from google.cloud import speech
    import os, datetime
    
    #print("pre-set 'client'!");
    #export GOOGLE_APPLICATION_CREDENTIALS = "";
    #export GOOGLE_APPLICATION_CREDENTIALS = "../../../arcane-geode-315302-b55530bd6b4f.json";
    #call("export GOOGLE_APPLICATION_CREDENTIALS = ../../../arcane-geode-315302-b55530bd6b4f.json");
    #call("export GOOGLE_APPLICATION_CREDENTIALS='../../../arcane-geode-315302-b55530bd6b4f.json'");
    os.environ['GOOGLE_APPLICATION_CREDENTIALS']= "/Users/vdo/Documents/Jeffrey/CMU/Courses/2021T2/49783/arcane-geode-315302-1851ff0299a3.json";
    os.environ['MAX_CONTENT_LENGTH']="16000";
    #putenv("GOOGLE_APPLICATION_CREDENTIALS", "../../../arcane-geode-315302-b55530bd6b4f.json");
    #print("nonsense");
    #print(os.environ);
    client = speech.SpeechClient(); #internal server error!
    
    audio = speech.RecognitionAudio(uri=gcs_uri)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.FLAC,
        sample_rate_hertz=16000,
        language_code="en-US",
        enable_word_time_offsets=True,
    )
    
    operation = client.long_running_recognize(config=config, audio=audio)
    
    print(str(datetime.datetime.now()));
    print("Waiting for operation to complete...");
    result = operation.result(timeout=900);
    print("Result retrieved!");
    print(str(datetime.datetime.now()));
    print(result.results);
    
    for result in result.results:
        alternative = result.alternatives[0]
        print("Transcript: {}".format(alternative.transcript))
        print("Confidence: {}".format(alternative.confidence))
        
        for word_info in alternative.words:
            word = word_info.word
            start_time = word_info.start_time
            end_time = word_info.end_time
            
            print(
                f"Word: {word}, start_time: {start_time.total_seconds()}, end_time: {end_time.total_seconds()}"
            )


# Create your views here.
def index(request):
    #transcribe_gcs_with_word_time_offsets("file:///Users/vdo/Desktop/lectureIntro.mov"); #"invalid GCS path"
    #transcribe_gcs_with_word_time_offsets("/Users/vdo/Desktop/lectureIntro.mov");
    #transcribe_gcs_with_word_time_offsets("gs://49783_input/LectureIntrd.mp4"); #fileNotFound error
    #transcribe_gcs_with_word_time_offsets("gs://49783_input/LectureIntro.mp4");
    transcribe_gcs_with_word_time_offsets("gs://49783_input/enunciate.mp4");
    return HttpResponse('Where can I upload, eh?');
