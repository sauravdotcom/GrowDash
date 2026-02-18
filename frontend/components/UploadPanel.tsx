"use client";

import { FormEvent, useRef, useState } from "react";

type UploadPanelProps = {
  uploading: boolean;
  onUpload: (file: File) => Promise<boolean>;
};

export function UploadPanel({ uploading, onUpload }: UploadPanelProps) {
  const [file, setFile] = useState<File | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file || uploading) {
      return;
    }

    const success = await onUpload(file);
    if (success) {
      setFile(null);
      if (inputRef.current) {
        inputRef.current.value = "";
      }
    }
  }

  return (
    <form className="upload-panel" onSubmit={handleSubmit}>
      <label htmlFor="tradebook">Upload Groww Tradebook CSV</label>
      <div className="upload-row">
        <input
          ref={inputRef}
          id="tradebook"
          name="tradebook"
          type="file"
          accept=".csv,text/csv"
          onChange={(event) => {
            const selected = event.target.files?.[0] || null;
            setFile(selected);
          }}
        />
        <button type="submit" disabled={!file || uploading}>
          {uploading ? "Uploading..." : "Upload"}
        </button>
      </div>
    </form>
  );
}
