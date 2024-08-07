def generate_yaml(names):
    template = """
apiVersion: eventing.knative.dev/v1
kind: Trigger
metadata:
  name: {name}trigger
  namespace: default
spec:
  broker: default
  filter:
    attributes:
      type: {name}msg
  subscriber:
    ref: 
      apiVersion: serving.knative.dev/v1
      kind: Service
      name: iso{name}
  delivery:
    retry: 0
"""
    for name in names:
        filename = f"trigger{name}.yaml"
        with open(filename, 'w') as f:
            f.write(template.format(name=name))
        print(f"Generated file: {filename}")

if __name__ == "__main__":
    names = ["omp","pyae","che","res","rot","mls","mlt","vid","web"]
    generate_yaml(names)
