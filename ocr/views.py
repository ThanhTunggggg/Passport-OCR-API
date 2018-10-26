from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.core.files.images import ImageFile
### Initializing the imports
import numpy as np
import json
#import cv2
import os
from django.views.decorators.csrf import csrf_exempt
import paho.mqtt.client as mqtt
from collections import OrderedDict
from django.http import JsonResponse, HttpResponse
import sys
if sys.version_info[0] == 3:
    from urllib.request import urlopen
else:
    # Not Python 3 - today, it is most likely to be Python 2
    # But note that this might need an update when Python 4
    # might be around one day
    from urllib import urlopen


# start off with defining a function to detect the URL requested which has the image for facial recognition
@csrf_exempt

def requested_url(request):
    #default value set to be false
    default = {"safely_executed": False} #because no detection yet
    ## between GET or POST, we go with Post request and check for https
    if request.method == "POST" and request.FILES["image"]:
        """
        if request.FILES.get("image", None) is not None:
            image_to_read = read_image(stream = request.FILES["image"])
        else: # URL is provided by the user
            url_provided = request.POST.get("url", None)
            if url_provided is None:
                default["error_value"] = "There is no URL Provided"
                return JsonResponse(default)
            image_to_read = read_image(url = url_provided)
        """
        #cv2.imwrite(filename , image_to_read)
        image = request.FILES['image']
        fs = FileSystemStorage()
        filename = fs.save(image.name, image)
        uploaded_file_url = fs.url(filename)
        print("Saved imgage: " + uploaded_file_url)
        filename = uploaded_file_url.split("/")[-1]
        cmd = "cd media \nmrz --json " + filename + " > " + filename +".json"
        os.system(cmd)
        with open("media/" + filename + ".json") as json_file:
            json_data = json.load(json_file, object_pairs_hook=OrderedDict)
            if json_data["mrz_type"] != None:
                #send_json_over_mqtt(json_data)
                default = format_response(json_data)
            else:
                #send_json_over_mqtt(json_data, vaild = False)
                pass
        """
        default.update({"#of_passport": len(values),
                        "passport":values,
                        "safely_executed": True })
        """
        print(default)
        #default = {'number': '990038535', 'names': 'VZOR', 'surname': 'SPECIMEN', 'date_of_birth': '1911/01/01', 'sex': 'Male'}
        response = JsonResponse(default)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS, POST, PUT"
        response["Access-Control-Max-Age"] = "1000"
        response["Access-Control-Allow-Headers"] = "X-Requested-With, Content-Type"
        return response #HttpResponse(json.dumps(default), content_type="application/javascript")
    response = JsonResponse(default)
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, OPTIONS, POST, PUT"
    response["Access-Control-Max-Age"] = "1000"
    response["Access-Control-Allow-Headers"] = "X-Requested-With, Content-Type"
    return response #HttpResponse(json.dumps(default), content_type="text/html")

def format_response(json_data):
    result = {}
    result["number"] = json_data["number"].replace("<","")
    result["names"] = json_data["names"].title()
    result["surname"] = json_data["surname"].title()
    result['date_of_birth'] = "19{2}/{1}/{0}".format(json_data['date_of_birth'][4:6], json_data['date_of_birth'][2:4], json_data['date_of_birth'][0:2])
    result['sex'] = "Female" if json_data["sex"] == "F" else "Male"
    return result
    
def read_image(path=None, stream=None, url=None):
    ##### primarily URL but if the path is None
    ## load the image from your local repository
    if path is not None:
        image = cv2.imread(path)
    else:
        if url is not None:
            response = urlopen(url)
            data_temp = response.read()
        elif stream is not None:
            #implying image is now streaming
            data_temp = stream.read()
        image = np.asarray(bytearray(data_temp), dtype="uint8")
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    return image

def correct_json(json_data):
    result = "{\"respcode\":0,\"errorDesc\":\"\",\"data\":[{\n"
    for key, val in json_data.items():
        if key == "valid_score":
            result = result + "  \"{0}\": {1}, \n".format(key, val)
        elif key.startswith("valid"):
            if val:
                result = result + "  \"{0}\": true, \n".format(key)
            else:
                result = result + "  \"{0}\": false, \n".format(key)
        elif key == "date_of_birth":
            tmp = "{0}-{1}-19{2}".format(val[2:4], val[4:6], val[0:2])
            result = result + "  \"{0}\": \"{1}\", \n".format(key, tmp)
        elif key == "walltime":
            result = result + "  \"{0}\": {1}, \n".format(key, val)
        elif key == "sex":
            if val == "F":
                result = result + "  \"{0}\": \"Female\", \n".format(key)
            else:
                result = result + "  \"{0}\": \"Male\", \n".format(key)
        elif key == "filename":
            result = result + "  \"{0}\": \"{1}\" \n".format(key, val) 
        else:
            result = result + "  \"{0}\": \"{1}\", \n".format(key, val) 
    result = result + "}]}"
    return result

def fill_json(json_data):
    if json_data["mrz_type"] != None:
        result = "{\"respcode\":0,\"errorDesc\":\"\",\"data\":[{\n" +\
                "  \"mrz_type\": \"\", \n" +\
                "  \"valid_score\": 100, \n" +\
                "  \"type\": \"\", \n" +\
                "  \"country\": \"\", \n" +\
                "  \"number\": \"{0}\", \n".format(json_data["number"].replace("<","")) +\
                "  \"date_of_birth\": \"{1}-{2}-19{0}\", \n".format(*(json_data["date_of_birth"][2*i:2*i+2] for i in range(3))) +\
                "  \"expiration_date\": \"\", \n" +\
                "  \"nationality\": \"\", \n" +\
                "  \"sex\": \"{0}\", \n".format("Female" if json_data["sex"] == "F" else "Male") +\
                "  \"names\": \"{0}\", \n".format(json_data["names"].title()) +\
                "  \"surname\": \"{0}\", \n".format(json_data["surname"].title()) +\
                "  \"personal_number\": \"\", \n" +\
                "  \"check_number\": \"\", \n" +\
                "  \"check_date_of_birth\": \"\", \n" +\
                "  \"check_ex piration_date\": \"\", \n" +\
                "  \"check_composite\": \"\", \n" +\
                "  \"check_personal_number\": \"\", \n" +\
                "  \"valid_number\": true, \n" +\
                "  \"valid_date_of_birth\": true, \n" +\
                "  \"valid_expiration_date\": true, \n" +\
                "  \"valid_composite\": true, \n" +\
                "  \"valid_personal_number\": true, \n" +\
                "  \"method\": \"\", \n" +\
                "  \"walltime\": 0, \n" +\
                "  \"filename\": \"\"\n" +\
                "}]}"
        return result

def send_json_over_mqtt(json_data, vaild = True):
    topic = "/device/hungdaibang01"
    if vaild:
        content = fill_json(json_data)
    else:
        content = "{\"respcode\":0,\"errorDesc\":\"\",\"data\":[{\n" +\
            "  \"mrz_type\": \"\", \n" +\
            "  \"valid_score\": 100, \n" +\
            "  \"type\": \"P<\", \n" +\
            "  \"country\": \"\", \n" +\
            "  \"number\": \"?\", \n" +\
            "  \"date_of_birth\": \"\", \n" +\
            "  \"expiration_date\": \"\", \n" +\
            "  \"nationality\": \"\", \n" +\
            "  \"sex\": \"\", \n" +\
            "  \"names\": \"\", \n" +\
            "  \"surname\": \"\", \n" +\
            "  \"personal_number\": \"\", \n" +\
            "  \"check_number\": \"4\", \n" +\
            "  \"check_date_of_birth\": \"4\", \n" +\
            "  \"check_ex piration_date\": \"3\", \n" +\
            "  \"check_composite\": \"4\", \n" +\
            "  \"check_personal_number\": \"0\", \n" +\
            "  \"valid_number\": true, \n" +\
            "  \"valid_date_of_birth\": true, \n" +\
            "  \"valid_expiration_date\": true, \n" +\
            "  \"valid_composite\": true, \n" +\
            "  \"valid_personal_number\": true, \n" +\
            "  \"method\": \"rescaled\", \n" +\
            "  \"walltime\": 0.1, \n" +\
            "  \"filename\": \"74.JPG\"\n" +\
            "}]}"
    
    #print(content)
    qos = 0
    broker = "gpay.vn"
    port = 1883
    clientId = "mqttest1"
    #content = json.dumps(json) # encode oject to JSON
    #print("\nConverting to JSON\n")
    #print ("data -type ",type(content))
    #print ("data out =",content)

    def on_connect(client, userdata, flags, rc):
        print("Connected with result code "+str(rc))
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        #client.subscribe("$SYS/#")

    def on_message(client, userdata, msg):
        print("message: " + msg.topic + " " + str(msg.payload))
    
    def on_publish(client,userdata,result):
        print("data published \n")

    client = mqtt.Client(client_id=clientId, protocol=mqtt.MQTTv31, transport="tcp")
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_publish = on_publish 
    print("Connecting to broker ",broker)
    client.connect(broker,port)
    #client.loop_start()
    #client.subscribe(topic)
    #time.sleep(3)
    #print("sending data")
    client.publish(topic, payload=content, qos=qos, retain=True)
    #time.sleep(10)
    #client.loop_stop()
    client.disconnect()









