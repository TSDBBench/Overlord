# Prometheus

## Links

* https://github.com/prometheus/prometheus
* https://github.com/prometheus/pushgateway
* https://github.com/prometheus/client_java
* https://prometheus.io/

## Information

* Uses LevelDB for indexes and uses a custom storage layer when persisiting data on the local filesystem
* "multi-dimensional data model"
* Features a flexible query language
  * Recording rules to save results of frequently needed expressions in separate time series
* Indirect pushing of time series data via pushgateway
  * Prometheus-Clients available to push data of the push metrics types counter, gauge, histogram or summary
    * Supported exposition format is the Protocol buffer format
    * No support of own timestamps, time of push is used instead
  * HTTP API to push to pushgateway
    * Supported exposition formats are plain text format and Protocol buffer format
    * Own timestamps can be used when using plain text format
* Two different query formats of ranges
  * Using offsets from the currect point of time and a granularity of s, m, h, d, w, y from there to include the desired time series data in a vector
    * Can be used by buitlin functions to calculate values as sum, avg, min, max
  * Using two timestamps rfc3339- or Unix-timestamps and a step size of ms, s, h, d, w, y to to include the desired time series in a matrix
    * No further postprocessing possible with builtin functions
* Prebuilt releases for prometheus and pushgateway are available

## Implementation Notes

* As custom timestamps are used in insert steps, the plaintext format was used
* As postprocessing functions are used in the scan steps, the vector result format was used
  * Timestamps were used to calculate offset and granularity to include the desired range of time series and overestimate the range as little as possible 


[back](../../)
