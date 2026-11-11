import mne
import numpy as np
from pathlib import Path

folder = Path(
    r"D:\LeakCheck_Data\MNE-eegbci-data\files\eegmmidb\1.0.0\S001"
)

for file in sorted(folder.glob("*.edf")):
    print("\n" + "=" * 50)
    print("FILE:", file.name)

    raw = mne.io.read_raw_edf(
        file,
        preload=False,
        verbose="ERROR"
    )

    print("Channels:", raw.info["nchan"])
    print("Sampling rate:", raw.info["sfreq"], "Hz")
    print("Duration:", round(raw.n_times / raw.info["sfreq"], 2), "seconds")
    print("Annotations:", len(raw.annotations))

    descriptions, counts = np.unique(
        raw.annotations.description,
        return_counts=True
    )

    print("Annotation descriptions:", dict(zip(descriptions, counts)))

    events, event_id = mne.events_from_annotations(
        raw,
        verbose="ERROR"
    )

    print("Event IDs:", event_id)

    event_counts = {
        name: int((events[:, 2] == code).sum())
        for name, code in event_id.items()
    }

    print("Event counts:", event_counts)

    raw.close()