## Kubernetes Resources

The repository contains the following deployment resources:

- `deployment.yaml`: Deploys the `game-service` application with 2 base replicas.
- `service.yaml`: Exposes the application through a `LoadBalancer` Service on port `80`, forwarding to container port `8000`.
- `hpa.yaml`: Configures a Horizontal Pod Autoscaler for the `game-service` Deployment with `minReplicas: 2`, `maxReplicas: 4`, and a CPU utilization target of `60%`.
- `spammer.yaml`: Runs a one-off load-generation Job against the in-cluster Service DNS name `http://game-service:80`.

Current resource settings in this repository:

- Deployment requests: `50m` CPU and `128Mi` memory
- Deployment limits: `150m` CPU and `256Mi` memory
- HPA range: 2 to 4 replicas
- Spammer profile: `500` RPS for `60` seconds after a `60` second warmup at `50` RPS

### Nodes

Command:

```bash
kubectl get nodes
```

Recorded output:

```text
NAME                                         STATUS   ROLES    AGE    VERSION
gk3-sre-cluster-nap-z0hdt6i8-ccbfd612-9l49   Ready    <none>   170m   v1.35.1-gke.1396002
```

### Pods

Command:

```bash
kubectl get pods
```

Recorded output:

```text
NAME                           READY   STATUS    RESTARTS   AGE
game-service-d9cc468d9-mmj7x   1/1     Running   0          174m
game-service-d9cc468d9-qxm7g   1/1     Running   0          174m
```

### Services

Command:

```bash
kubectl get svc
```

Recorded output:

```text
NAME           TYPE           CLUSTER-IP       EXTERNAL-IP    PORT(S)        AGE
game-service   LoadBalancer   34.118.225.128   34.118.34.44   80:32469/TCP   165m
kubernetes     ClusterIP      34.118.224.1     <none>         443/TCP        24h
```

## Load Test Procedure

The load test was started with:

```bash
kubectl apply -f spammer.yaml
```

Recorded pod state after creating the Job:

```text
NAME                           READY   STATUS      RESTARTS   AGE
game-service-d9cc468d9-mmj7x   1/1     Running     0          3h42m
game-service-d9cc468d9-qxm7g   1/1     Running     0          3h42m
spammer-qnsbn                  0/1     Completed   0          5m52s
```

The Job logs were viewed with:

```bash
kubectl logs spammer-qnsbn
```

## Recorded Load Test Results

### Scenario 1: Baseline at 1000 RPS

Profile:

- RPS: `1000`
- Duration: `60s`
- Warmup: `60s @ 100 req/s`
- Endpoints: `get_stats`, `update_player`

Recorded output:

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

This baseline configuration did not sustain the requested throughput and produced a high 5xx error rate.

### Scenario 2: Reduced Load at 500 RPS

Profile:

- RPS: `500`
- Duration: `60s`
- Warmup: `60s @ 50 req/s`
- Endpoints: `get_stats`, `update_player`

Recorded output:

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

Reducing the offered load improved the success rate, but the service still produced a material number of 5xx responses.

### Scenario 3: HPA with Maximum 4 Replicas at 30% CPU Utilization

Recorded output:

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

This configuration significantly improved throughput and reduced server errors to a negligible level. The lower CPU utilization target was used to encourage earlier scale-out for this workload pattern.

### Scenario 4: CPU Request Reduced to 50m with 60% CPU Utilization Target

Recorded output:

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

This was the strongest recorded result in the verification notes. Under the `500` RPS profile, the service completed all `30000` requests successfully with no 5xx responses.

## Conclusion

The verification data shows a clear progression:

- The baseline deployment could not sustain `1000` RPS reliably.
- Reducing traffic to `500` RPS improved results, but did not eliminate server-side failures.
- Adding autoscaling headroom and tuning CPU-based scaling materially improved performance.
- The best recorded result came from reducing the CPU request to `50m` while using a `60%` CPU utilization target, resulting in full success at `500` RPS.

This repository is therefore configured around a scale-out approach rather than permanently over-provisioning CPU for a fixed number of replicas.
