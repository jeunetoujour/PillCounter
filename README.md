# Pill Counter Web Service 
This project was made to solve a problem of counting pills quickly and accurately. I don't want a machine and I just want to take a picture.
There are many issues with just taking a picture of pills as you know. Lighting effects how computer vision works a ton, along with writing on the pill,
and contrast of the pills vs the background color.

I can sort the pills by shape such as Sphere or Oblong, and attempt to count.a

The pics directory has many test pictures to play with. The expectation is to have a very dark background against the pills, so there is high contrast.
test.sh is a quick tester to test all the pictures in a directory against the web service and find any that are not 100% accurate
Set debug=true if you wish to have it print out all the steps and images as it works.

TESTING:

Run this locally such that it requests you to hit it like so(I use postman):
POST http://localhost:5000/upload
Body is: key=file value=image you are uploading
Returns: count=some number

After its done, it will save the processed file in your /uploads directory. You can call the service to get the image.
GET http://localhost:5000/uploads/orig_test2.jpg   (example)
Returns processed image with count and type in image.

Example of a circle pill:
![Original Image](https://github.com/jeunetoujour/PillCounter/blob/master/pics/orig_test2.jpg)<!-- .element height="50%" width="50%" -->
![Processed Image](https://github.com/jeunetoujour/PillCounter/blob/master/pics/cv_orig_test2.jpg)<!-- .element height="25%" width="25%" -->

Oblong Pills:
![Original Image](https://github.com/jeunetoujour/PillCounter/blob/master/pics/fat_test_2.jpg)<!-- .element height="25%" width="25%" -->
![Processed Image](https://github.com/jeunetoujour/PillCounter/blob/master/pics/cv_fat_test_2.jpg)<!-- .element height="25%" width="25%" -->

Superman Pills:
![Original Image](https://github.com/jeunetoujour/PillCounter/blob/master/pics/orig_test7.jpg)<!-- .element height="25%" width="25%" -->
![Processed Image](https://github.com/jeunetoujour/PillCounter/blob/master/pics/cv_orig_test7.jpg)<!-- .element height="25%" width="25%" -->
