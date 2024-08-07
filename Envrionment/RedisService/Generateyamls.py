def generate_yaml(names):
    template = """
apiVersion: v1
kind: Service
metadata:
  name: {name}datasvc
spec:
  type: NodePort
  ports:
  - port: 6379
    targetPort: 6379
  selector:
    app: redis{name}
"""
    for name in names:
        filename = f"Svc{name}.yaml"
        with open(filename, 'w') as f:
            f.write(template.format(name=name))
        print(f"Generated file: {filename}")

if __name__ == "__main__":
    names = ["res","rot","mls","mlt","vid","web"]
    generate_yaml(names)
