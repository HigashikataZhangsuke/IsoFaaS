#cd cnn_serving
#kubectl apply -f cnn_serving.yaml
#
#cd ../img_res
#kubectl apply -f img_res.yaml
#
#cd ../img_rot
#kubectl apply -f img_rot.yaml
#
#cd ../ml_train
#kubectl apply -f ml_train.yaml
#
#cd ../vid_proc
#kubectl apply -f vid_proc.yaml

#cd ./omp_test
#kubectl apply -f omp.yaml

#cd ..

#cd ./pyaes
#kubectl apply -f pyae.yaml

#cd ./alu
#kubectl apply -f pyae.yaml

#cd ..
cd ./testyamls
kubectl apply -f alu.yaml
kubectl apply -f omp.yaml
