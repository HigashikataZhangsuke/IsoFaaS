def generate_yaml(names):
    template = """
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: iso{name}
  namespace: default
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "1"
        autoscaling.knative.dev/maxScale: "1"
    spec:
      containers:
        - name: flmls
          image: yzzhangllm/flask{name}:latest
          ports:
            - containerPort: 12346

        - name : mls
          image: yzzhangllm/{name}ex:latest

      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                  - key: vm
                    operator: In
                    values:
                      - MT  

"""
    for name in names:
        filename = f"isoex{name}.yaml"
        with open(filename, 'w') as f:
            f.write(template.format(name=name))
        print(f"Generated file: {filename}")

if __name__ == "__main__":
    names = ["omp","pyae","che","res","rot","alu","mlt","vid","web"]
    generate_yaml(names)
