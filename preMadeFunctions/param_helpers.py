def get_time(req_type, seconds):
    seconds = int(seconds)

    d = seconds // (60 * 60 * 24)
    h = (seconds % (60 * 60 * 24)) // (60 * 60)
    m = (seconds % (60 * 60)) // 60
    s = seconds % 60

    if req_type == "uptime":
        if d != 0:
            timeval = f"{d}d {h}h {m}m {s}s"
        elif h != 0:
            timeval = f"{h}h {m}m {s}s"
        else:
            timeval = f"{m}m {s}s"
    else:
        timeval = f"{d:02d}:{h:02d}:{m:02d}:{s:02d}"

    return timeval
