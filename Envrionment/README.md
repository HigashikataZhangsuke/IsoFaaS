# Currently provides env setting for single node tests
The Broker-Triggers and Redis services are up to date, and won't interf each other.
If you need to do multiple node tests, please first modify the svcyamls. They need to apply they "anti-affinity".
Besides, one way of quick doing multiple node tests is to use the keep warm way. So far you do not know what will happen if you use the knative's autoscaling methods. If you really want to test this need to apply GC and Global scheduler here.
