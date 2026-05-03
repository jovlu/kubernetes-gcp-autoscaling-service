# Get all cluster nodes:

```powershell
kubectl get nodes
```

response:

```text
NAME                                         STATUS   ROLES    AGE    VERSION
gk3-sre-cluster-nap-z0hdt6i8-ccbfd612-9l49   Ready    <none>   170m   v1.35.1-gke.1396002
```

## Get all pods:

```powershell
kubectl get pods
```

response:

```text
NAME                           READY   STATUS    RESTARTS   AGE
game-service-d9cc468d9-mmj7x   1/1     Running   0          174m
game-service-d9cc468d9-qxm7g   1/1     Running   0          174m
```

## Get all services:

```powershell
kubectl get svc
```

response:

```text
NAME           TYPE           CLUSTER-IP       EXTERNAL-IP    PORT(S)        AGE
game-service   LoadBalancer   34.118.225.128   34.118.34.44   80:32469/TCP   165m
kubernetes     ClusterIP      34.118.224.1     <none>         443/TCP        24h
```

## Created a new job:

```powershell
kubectl apply -f spammer.yaml
kubectl get pods
```

response:

```text
PS C:\Users\Jovan\Desktop\game-service\game-service> kubectl get pods
NAME                           READY   STATUS      RESTARTS   AGE
game-service-d9cc468d9-mmj7x   1/1     Running     0          3h42m
game-service-d9cc468d9-qxm7g   1/1     Running     0          3h42m
spammer-qnsbn                  0/1     Completed   0          5m52s
```

## Viewed logs:

```powershell
kubectl logs spammer-qnsbn
```

```text
Spamming http://game-service:80
  RPS         : 1000
  Duration    : 60s
  Warmup      : 60s @ 100 req/s
  Endpoints   : ['get_stats', 'update_player']

Warming up for 60s at 100 req/s...
Warmup done.
Sending 60000 requests at 1000 req/s for 60s...

============================================================
SPAMMER REPORT
============================================================
Total requests : 60000
Wall time      : 157.11s
Throughput     : 381.9 req/s
Success (2xx)  : 9993
Client err(4xx): 0
Errors/5xx     : 50007

Latency (ms):
  avg : 19252.3
  p50 : 11760.8
  p95 : 63478.2
  p99 : 66420.9
  min : 25.1
  max : 68062.0
============================================================
```

We can now decrease some env vars, as well as to increase resources such as RAM or CPU, or replicas, in deployment.yaml to get a higher amount of 2xx responses

## Decreasing the spammer RPS to 500

Decreasing the spammer RPS to 500, with no change to the CPU or RAM (which essentially isn't an improvement, but doing HPA with even 6 or 4 replicas is stopped by Google)
Note: Increasing the CPU limit to 400m while holding RPS at 1000 dramatically increased the success rate

```text
Spamming http://game-service:80
  RPS         : 500
  Duration    : 60s
  Warmup      : 60s @ 50 req/s
  Endpoints   : ['get_stats', 'update_player']

Warming up for 60s at 50 req/s...
Warmup done.
Sending 30000 requests at 500 req/s for 60s...

============================================================
SPAMMER REPORT
============================================================
Total requests : 30000
Wall time      : 79.02s
Throughput     : 379.6 req/s
Success (2xx)  : 22383
Client err(4xx): 0
Errors/5xx     : 7617

Latency (ms):
  avg : 2767.1
  p50 : 833.9
  p95 : 17744.1
  p99 : 26309.3
  min : 9.7
  max : 30814.5
============================================================
```

## If we apply max 4 replicas at 30% CPU utilisation

```text
Spamming http://game-service:80
  RPS         : 500
  Duration    : 60s
  Warmup      : 60s @ 50 req/s
  Endpoints   : ['get_stats', 'update_player']

Warming up for 60s at 50 req/s...
Warmup done.
Sending 30000 requests at 500 req/s for 60s...

============================================================
SPAMMER REPORT
============================================================
Total requests : 30000
Wall time      : 61.75s
Throughput     : 485.8 req/s
Success (2xx)  : 29982
Client err(4xx): 0
Errors/5xx     : 18

Latency (ms):
  avg : 1411.7
  p50 : 254.5
  p95 : 11792.2
  p99 : 18181.3
  min : 6.9
  max : 27048.5
============================================================
```

And 30% is for the other pods to have time to wake up, obviously it is for this use case only.

## Reducing the requested CPU to 50m

Reducing the requested CPU to 50m (increasing CPU util to 60%)

```text
Spamming http://game-service:80
  RPS         : 500
  Duration    : 60s
  Warmup      : 60s @ 50 req/s
  Endpoints   : ['get_stats', 'update_player']

Warming up for 60s at 50 req/s...
Warmup done.
Sending 30000 requests at 500 req/s for 60s...

============================================================
SPAMMER REPORT
============================================================
Total requests : 30000
Wall time      : 60.09s
Throughput     : 499.2 req/s
Success (2xx)  : 30000
Client err(4xx): 0
Errors/5xx     : 0

Latency (ms):
  avg : 75.1
  p50 : 55.2
  p95 : 181.2
  p99 : 381.5
  min : 5.9
  max : 1409.1
============================================================
```

## Final selected scaling configuration:

- Deployment starts with 2 replicas.
- HPA scales from 2 to 5 replicas at a 30% CPU utilization target.
- HPA scale-up behavior allows up to 3 pods or 200% growth every 15s.
- HPA scale-down stabilization is 60s.
- Per-pod request: 50m CPU, 52Mi memory.
- Per-pod limit: 120m CPU, 128Mi memory.
- Uvicorn access logs are disabled to reduce per-request overhead without changing application source code.
- Spammer profile: 650 RPS for 120s after 60s warmup at 150 RPS.

The final configuration was selected through an iterative tuning process. I adjusted:

- game-service CPU and memory requests/limits
- HPA min/max replicas
- HPA CPU utilization target
- HPA scale-up and scale-down behavior
- spammer warmup duration and warmup RPS
- spammer load-test RPS

The goal was to keep the idle deployment small, allow automatic scale-out during the warmup phase, and find the highest tested spike load that still kept the error rate low.

## Final selected spike result:

```text
Spamming http://game-service:80
  RPS         : 650
  Duration    : 120s
  Warmup      : 60s @ 150 req/s
  Endpoints   : ['get_stats', 'update_player']

Warming up for 60s at 150 req/s...
Warmup done.
Sending 78000 requests at 650 req/s for 120s...

============================================================
SPAMMER REPORT
============================================================
Total requests : 78000
Wall time      : 120.28s
Throughput     : 648.5 req/s
Success (2xx)  : 77857
Client err(4xx): 0
Errors/5xx     : 143

Latency (ms):
  avg : 839.1
  p50 : 180.1
  p95 : 2279.8
  p99 : 16645.3
  min : 5.5
  max : 30557.3
============================================================
```

This is the selected scaling result: 143 errors out of 78000 requests, or about 0.183% 5xx, while demonstrating automatic scale-out from the 2-replica baseline.
