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
- capture, request, render, detection, server, and full-pipeline timing.

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
after the returned JPEG is decoded and the browser crosses one
`requestAnimationFrame` boundary. It therefore includes:

```text
capture and browser JPEG
  -> HTTP upload
  -> server decode/detect/blur/encode
  -> HTTP download
  -> browser image decode
  -> animation-frame boundary
```

It is more complete than the earlier status metric, which started after capture
and ended before image decode/render. It still does not prove that every sample
represents a unique source-video frame or that a physical display completed a
pixel refresh.

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
- `zero_face_samples`: samples where the detector returned no face.
- `slowest_frames`: the 20 samples with the largest `pipeline_ms`, including
  their capture, request, render, detector, server, and face-count fields.

The on-page panel shows a rolling window of the latest 300 samples. After the
source stops, it shows the full run summary. The exported JSON always contains
every retained sample and a full summary for each session.

## Analysis Checklist

When sharing an export, separately state:

- browser and version;
- whether the source was camera or screen;
- expected visible-face count and any observed misses or blur flicker;
- approximate CPU and RAM use;
- whether the tab was visible, minimized, or covered;
- any competing workload.

Do not attach screenshots, face media, names, or private source details unless
they are explicitly authorized and necessary for a separate accuracy review.
