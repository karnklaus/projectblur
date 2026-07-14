# ProjectBlur Browser Metrics

## Purpose

The live browser prototype automatically records performance metadata so short
lag spikes are not lost when the status text updates. Metrics stay in browser
memory until the page is reloaded or the user resets them. Nothing is uploaded
or persisted by the metrics recorder.

Use **Export metrics** after a camera or screen-share run to download JSON that
can be attached for analysis.

## Privacy Boundary

The export contains:

- detector health metadata;
- source kind and dimensions;
- configured blur, padding, and capture-size settings;
- relative frame number and elapsed time;
- face count;
- capture, request, response-image decode, detection, server, and processing
  pipeline timing;
- non-blocking presentation-callback delay and document visibility state;
- warm-up and capture-stall markers.

It does not contain frames, image bytes, face crops, embeddings, names, browser
history, page URLs, video titles, audio, or identity data. A face count is not
ground truth and cannot establish whether every visible face was detected.

## Session Behavior

- Starting a camera or screen source starts a new session automatically.
- Stopping or replacing the source finalizes the current session and summary.
- Multiple sessions can be included in one export during the same page visit.
- **Reset log** deletes metrics from browser memory. If a source is active, a
  fresh session begins immediately.
- Each session stores at most 50,000 samples. Additional iterations are counted
  in `samples_dropped_after_cap` rather than growing memory without limit.

## Timing Definition

`pipeline_ms` starts before drawing and JPEG-encoding the source frame. It ends
after the returned JPEG is decoded. It therefore includes:

```text
capture and browser JPEG
  -> HTTP upload
  -> server decode/detect/blur/encode
  -> HTTP download
  -> browser image decode
```

Schema v2 does not block processing while waiting for `requestAnimationFrame`.
Instead, `presentation_delay_ms` records the next callback opportunistically.
It remains `null` while pending or when presentation timing was not scheduled
because the document was hidden. This callback delay does not prove that a
physical display completed a pixel refresh.

Each sample records document visibility at the start and end of processing.
The session also records `visibility_events`. This allows background-tab
throttling to be separated from detector and server latency.

The first 30 samples are marked `warmup: true`. A sample is marked
`capture_stall: true` when capture and JPEG encoding take more than 50 ms.

## Summary Fields

- `throughput_fps`: `1000 / mean(pipeline_ms)`.
- `median_pipeline_ms`: nearest-rank 50th percentile.
- `p95_pipeline_ms`: nearest-rank 95th percentile.
- `p99_pipeline_ms`: nearest-rank 99th percentile.
- `maximum_pipeline_ms`: slowest recorded iteration.
- `below_30_fps_count`: samples slower than 33.333 ms.
- `below_30_fps_percent`: percentage of recorded samples slower than 33.333 ms.
- `p95_detection_ms`: detector-stage P95 reported by the server.
- `p95_server_ms`: complete server-stage P95 reported by the server.
- `p95_capture_ms`: browser capture/JPEG P95.
- `p95_decode_ms`: returned-image decode P95.
- `capture_stall_count`: samples whose capture/JPEG stage exceeded 50 ms.
- `hidden_at_start_count` and `hidden_at_end_count`: samples processed while
  the ProjectBlur document was not visible.
- `presentation_observed_count`: samples with a completed non-blocking
  animation-frame observation.
- `presentation_pending_count`: callbacks still pending when summarized.
- `presentation_not_scheduled_hidden_count`: samples for which callback timing
  was intentionally skipped because the page was hidden.
- `p95_presentation_delay_ms`: P95 of completed animation-frame observations.
- `steady_state`: the timing summary with the first 30 warm-up samples removed.
- `zero_face_samples`: samples where the detector returned no face.
- `slowest_frames`: the 20 samples with the largest `pipeline_ms`, including
  their capture, request, decode, presentation, visibility, detector, server,
  warm-up, capture-stall, and face-count fields.

The on-page panel shows a rolling window of the latest 300 samples. After the
source stops, it shows the full run summary. The exported JSON always contains
every retained sample and a full summary for each session.

## Schema History

- Schema v1 included a blocking animation-frame boundary in `pipeline_ms`.
  This could stop the entire sequential processing loop when the ProjectBlur
  tab was hidden or the browser throttled presentation callbacks.
- Schema v2 ends `pipeline_ms` after image decode and records presentation delay
  without awaiting it. It also adds visibility events, warm-up markers,
  capture-stall markers, and a steady-state summary.

Do not combine schema v1 and schema v2 pipeline values into one distribution.

## Analysis Checklist

When sharing an export, separately state:

- browser and version;
- whether the source was camera or screen;
- expected visible-face count and any observed misses or blur flicker;
- approximate CPU and RAM use;
- whether the tab was covered or minimized; visibility transitions are also
  captured automatically where the browser exposes them;
- any competing workload.

Do not attach screenshots, face media, names, or private source details unless
they are explicitly authorized and necessary for a separate accuracy review.
