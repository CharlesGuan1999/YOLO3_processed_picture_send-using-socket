
import cv2 as cv
import sys
import numpy as np
import os.path
import time, socket, struct

# Initialize the parameters
confThreshold = 0.5  #Confidence threshold
nmsThreshold = 0.4   #Non-maximum suppression threshold
inpWidth = 416       #Width of network's input image
inpHeight = 416      #Height of network's input image

# 客户端退出
class FError(Exception):
    pass
# 客户端回应异常
class ResponseError(Exception):
    pass
	
# Load names of classes
classesFile = "coco.names"
classes = None
with open(classesFile, 'rt') as f:
    classes = f.read().rstrip('\n').split('\n')

# Give the configuration and weight files for the model and load the network using them.
modelConfiguration = "yolov3.cfg"
modelWeights = "yolov3.weights"

net = cv.dnn.readNetFromDarknet(modelConfiguration, modelWeights)
net.setPreferableBackend(cv.dnn.DNN_BACKEND_OPENCV)
net.setPreferableTarget(cv.dnn.DNN_TARGET_CPU)

# Get the names of the output layers
def getOutputsNames(net):
    # Get the names of all the layers in the network
    layersNames = net.getLayerNames()
    # Get the names of the output layers, i.e. the layers with unconnected outputs
    return [layersNames[i[0] - 1] for i in net.getUnconnectedOutLayers()]

# Draw the predicted bounding box
def drawPred(classId, conf, left, top, right, bottom):
    # Draw a bounding box.
    cv.rectangle(frame, (left, top), (right, bottom), (255, 178, 50), 3)
    
    label = '%.2f' % conf
        
    # Get the label for the class name and its confidence
    if classes:
        assert(classId < len(classes))
        label = '%s:%s' % (classes[classId], label)
    
    print("class: ", classes[classId])

    #Display the label at the top of the bounding box
    labelSize, baseLine = cv.getTextSize(label, cv.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    top = max(top, labelSize[1])
    cv.rectangle(frame, (left, top - round(1.5*labelSize[1])), (left + round(1.5*labelSize[0]), top + baseLine), (255, 255, 255), cv.FILLED)
    cv.putText(frame, label, (left, top), cv.FONT_HERSHEY_SIMPLEX, 0.75, (0,0,0), 1)
    # 此处将抛出识别到的人	
    if conf >= 0.7 and classes[classId] == 'person':
	    return True
    return False

# Remove the bounding boxes with low confidence using non-maxima suppression
def postprocess(frame, outs):
    frameHeight = frame.shape[0]
    frameWidth = frame.shape[1]
    tag = False
    # Scan through all the bounding boxes output from the network and keep only the
    # ones with high confidence scores. Assign the box's class label as the class with the highest score.
    classIds = []
    confidences = []
    boxes = []
    for out in outs:
        for detection in out:
            scores = detection[5:]
            classId = np.argmax(scores)
            confidence = scores[classId]
            if confidence > confThreshold:
                center_x = int(detection[0] * frameWidth)
                center_y = int(detection[1] * frameHeight)
                width = int(detection[2] * frameWidth)
                height = int(detection[3] * frameHeight)
                left = int(center_x - width / 2)
                top = int(center_y - height / 2)
                classIds.append(classId)
                confidences.append(float(confidence))
                boxes.append([left, top, width, height])

    # Perform non maximum suppression to eliminate redundant overlapping boxes with
    # lower confidences.
    indices = cv.dnn.NMSBoxes(boxes, confidences, confThreshold, nmsThreshold)
    for i in indices:
        i = i[0]
        box = boxes[i]
        left = box[0]
        top = box[1]
        width = box[2]
        height = box[3]
		# 只要检测到“人”，返回时将报警
        if drawPred(classIds[i], confidences[i], left, top, left + width, top + height) == True:
            tag = True

    return tag



#开启TCP服务
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 测试请改成127.0.0.1
host = "127.0.0.1" # 树莓派IP地址
port = 7777
#连接树莓派服务端
client.connect((host, port))
#发送给服务器的message列表
messageBox = ['picture', 'danger', 'quit']

# 图片地址
# 正常的图片日志log 存储在工作目录的picture_log文件夹中
# 危险的图片存储在工作目录的picture_log文件夹中,并以danger_py结尾
image_path = ""
outputFile = ""
# log图片计数器
i = 1

tik = time.time()
new_filename = ''
#开始人物检测
while 1:
    # 30秒后自动退出
    if time.time() - tik > 30:
        raise FError("time is up!")
		
    try:
        #告诉服务器发送图片
        client.send(messageBox[0].encode())
        fileinfo_size = struct.calcsize('128sl')
        #接受图片
        buf = client.recv(fileinfo_size)
        if buf:
            filename, filesize = struct.unpack('128sl', buf)
            fn = filename.strip('\00'.encode())

            # 新文件将存储在picture_log文件夹里
            new_filename = os.path.join('./', 'picture_log/' + "%s."%i +fn.decode())
            i = i + 1
            print ('file new name is {0}, filesize if {1}'.format(new_filename, filesize))

            recvd_size = 0 # 定义已接收文件的大小
            fp = open(new_filename, 'wb')
            print ('start receiving...')

            # 开始接收文件内容
            while not recvd_size == filesize:
                if filesize - recvd_size > 1024:
                    data = client.recv(1024)
                    recvd_size += len(data)
                else:
                    data = client.recv(filesize - recvd_size)
                    recvd_size = filesize
                fp.write(data)
            fp.close()
            print ('end receive...')

        # 得到存入的图片地址
        image_path = new_filename
        if (image_path != ''):
            # Open the image file
            if not os.path.isfile(image_path):
                print("Input image file ", image_path, " doesn't exist")
                sys.exit(1)
            cap = cv.VideoCapture(image_path)
            #存储处理结束的图片地址
            outputFile = image_path[:-4]+'_danger_py.jpg'
        else:
            raise FError("No picture")


        while cv.waitKey(1) < 0:

            # get frame from the video
            hasFrame, frame = cap.read()

            # Stop the program if reached end of video
            if not hasFrame:
                print("Done processing !!!")
                cv.waitKey(3000)
                # Release device
                cap.release()
                break

            # Create a 4D blob from a frame.
            blob = cv.dnn.blobFromImage(frame, 1/255, (inpWidth, inpHeight), [0,0,0], 1, crop=False)

            # Sets the input to the network
            net.setInput(blob)

            # Runs the forward pass to get output of the output layers
            outs = net.forward(getOutputsNames(net))

            # Remove the bounding boxes with low confidence
            # 如果此函数返回值为danger，则将通知树莓派
            if postprocess(frame, outs) == True:
                
                t, _ = net.getPerfProfile()
                label = 'Inference time: %.2f ms' % (t * 1000.0 / cv.getTickFrequency())
                cv.putText(frame, label, (0, 15), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255))
                # 存储出现人的图像
                cv.imwrite(outputFile, frame.astype(np.uint8))
                print("Output file is stored as ", outputFile)
				# 告诉服务器出现危险（发现了人）
                client.send(messageBox[1].encode())
                buf = client.recv(1024)
                if (buf.decode() != 'ring_finished'):
                    raise ResponseError("ring response:")
				
        # 4秒申请一次picture
        time.sleep(2)
    except FError as e:
        client.send(messageBox[2].encode())
        client.close()
        print("client close")
        print(e)
    # 键盘中断退出
    except ResponseError as e:
        client.send(messageBox[2].encode())
        client.close()
        print("response error")
        print(e)
		
    except KeyboardInterrupt:
        client.send(messageBox[2].encode())
        client.close()
