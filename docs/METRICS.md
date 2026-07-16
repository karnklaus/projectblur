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
- capture/detector-JPEG, request, source-resolution render, detection, server,
  and processing pipeline timing;
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

In schema v3, `pipeline_ms` starts before copying the source-resolution frame
and drawing/JPEG-encoding its reduced detector copy. It ends after the browser
applies returned face boxes to the source-resolution output canvas. It includes:

```text
source-resolution frame copy and reduced browser JPEG
  -> HTTP upload
  -> server decode/detect
  -> HTTP bounding-box response
  -> source-resolution browser canvas render and regional blur
```

Schema v3 does not block processing while waiting for `requestAnimationFrame`.
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
- `p95_render_ms`: source-resolution canvas copy and regional-blur P95.
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
  their capture, request, render, presentation, visibility, detector, server,
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
- Schema v3 replaces the returned-JPEG stage with a bounding-box response and
  source-resolution browser render. It replaces `decode_ms`/`p95_decode_ms`
  with `render_ms`/`p95_render_ms`.

Do not combine schema v1, v2, and v3 pipeline values into one distribution.

## CLI benchmark records

Successful runs of `benchmarks/retinaface_backend_benchmark.py` and
`benchmarks/virtual_camera_output_benchmark.py` automatically write one unique
JSON record under `artifacts/benchmarks/`. An optional `--output` chooses an
exact new file, but neither script overwrites existing evidence.

The common provenance fields are:

- `run_id` and `recorded_at_utc`: microsecond UTC identity and start time;
- `environment`: OS, architecture, processor identifier, logical processor
  count, Python/process architecture, and relevant installed package versions;
- `repository.commit` and `repository.worktree_dirty`: source provenance;
- benchmark configuration and raw result values, without rounded-only tables;
- `limitations`: what the run cannot establish;
- detector model path relative to the repository, byte size, and SHA-256 when
  the adapter exposes a local model file.

The automatic files are raw run evidence. Do not silently delete a slow run,
rename a synthetic run as an accuracy experiment, or edit its measured values.
If a run is invalid, retain it and document the exclusion reason in
`docs/EXPERIMENTS.md`. Curated experiment artifacts may combine immutable raw
runs, but must name every source file and state the aggregation method.

Browser sessions are the deliberate exception to repository-side automatic
storage: the page keeps them in browser memory to avoid silently persisting
capture-related metadata. For paper work, stop the source and use **Export
metrics** after every session before reloading or resetting the page, then
record the exported filename and SHA-256 in the matching experiment artifact.
An unexported browser session is not durable evidence.

For paper use, define the comparison before running it, keep configuration and
machine conditions fixed, and collect repeated trials. Report sample count,
warm-up, input type and resolution, mean/median/P95 (and variability across
runs), hardware/software versions, Git state, model hash, inclusion/exclusion
rules, and limitations. Synthetic zero-face latency must never be presented as
accuracy, recall, privacy-safety, or real-scene end-to-end evidence.

## Virtual-camera benchmark metrics

`benchmarks/virtual_camera_output_benchmark.py` produces a separate schema. It
must not be merged with browser schema v1/v2/v3 samples. The input is a generated
BGRA frame; no image or biometric data is retained.

- `publisher.mean_publish_ms` and `p95_publish_ms`: Python header plus BGRA copy
  time into the latest-frame mapping.
- `camera_reader.delivered_fps`: samples returned by a Media Foundation source
  reader divided by the measured interval.
- `unique_source_frames`: distinct even publisher sequence values observed.
- `source_frames_not_observed`: sequence positions skipped between the first
  and last observed source frame.
- `duplicate_samples`: delivered non-fallback samples that repeat a source
  sequence.
- `fallback_samples`: black samples caused by absent, stale, malformed, or
  wrong-sized input.
- `p95_frame_age_ms`: source publish timestamp to source-reader arrival. This
  includes Media Foundation buffering and is not detector or glass-to-glass
  latency.
- `estimated_pipeline_fps_with_publish`: optional serial-cost calculation using
  `--baseline-fps`; it is not a measured integrated detector FPS.

Record resolution, target frame rate, warm-up, duration, OS build, Python
version, installed DLL hash, and whether a detector/capture source was included.

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
