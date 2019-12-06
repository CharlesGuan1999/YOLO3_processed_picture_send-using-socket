# YOLO3_processed_picture_send-using-socket

1.首先运行virtual server.py开启服务器端，主要负责发送图片数据；再运行object_detc_client.py开启客户端，接受图片数据，并用yolo3进行人像判定

2.客户端将收到的图片全部存储于picture_log文件夹中；如果处理到有人像的图片，将处理结果也存储在log中，并将文件名加上_danger_py后缀

3.YOLOv3 model相关代码参考以下博客修改
  https://www.learnopencv.com/deep-learning-based-object-detection-using-yolov3-with-opencv-python-c/
