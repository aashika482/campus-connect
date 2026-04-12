import { useState, useRef } from 'react'

const CLOUD_NAME    = import.meta.env.VITE_CLOUDINARY_CLOUD_NAME
const UPLOAD_PRESET = import.meta.env.VITE_CLOUDINARY_UPLOAD_PRESET

interface ImageUploadProps {
  value?: string
  onChange: (url: string) => void
  error?: string
}

export function ImageUpload({ value, onChange, error }: ImageUploadProps) {
  const [uploading, setUploading]     = useState(false)
  const [progress, setProgress]       = useState(0)
  const [uploadError, setUploadError] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  // ── Fallback: Cloudinary not configured ─────────────────
  if (!CLOUD_NAME || !UPLOAD_PRESET) {
    return (
      <div>
        <input
          className="inp"
          value={value ?? ''}
          onChange={e => onChange(e.target.value)}
          placeholder="Paste poster image URL"
        />
        <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)', marginTop: 6 }}>
          Set up Cloudinary in .env for drag-and-drop upload
        </div>
      </div>
    )
  }

  // ── Upload via XHR so we get progress events ─────────────
  const handleFile = async (file: File) => {
    if (!file.type.startsWith('image/')) {
      setUploadError('Please select an image file')
      return
    }
    if (file.size > 10 * 1024 * 1024) {
      setUploadError('File is too large (max 10 MB)')
      return
    }

    setUploading(true)
    setUploadError('')
    setProgress(0)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('upload_preset', UPLOAD_PRESET)

    try {
      const secureUrl = await new Promise<string>((resolve, reject) => {
        const xhr = new XMLHttpRequest()

        xhr.upload.addEventListener('progress', e => {
          if (e.lengthComputable) setProgress(Math.round((e.loaded / e.total) * 100))
        })
        xhr.addEventListener('load', () => {
          if (xhr.status === 200) {
            resolve(JSON.parse(xhr.responseText).secure_url)
          } else {
            reject(new Error('Upload failed'))
          }
        })
        xhr.addEventListener('error', () => reject(new Error('Network error')))

        xhr.open('POST', `https://api.cloudinary.com/v1_1/${CLOUD_NAME}/image/upload`)
        xhr.send(formData)
      })

      onChange(secureUrl)
    } catch {
      setUploadError('Upload failed — please try again')
    } finally {
      setUploading(false)
      setProgress(0)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
    e.target.value = '' // reset so the same file can be re-selected
  }

  const handleRemove = () => {
    onChange('')
    setUploadError('')
  }

  // ── Preview (upload done) ────────────────────────────────
  if (value && !uploading) {
    return (
      <div style={{
        position: 'relative',
        borderRadius: 12,
        overflow: 'hidden',
        border: '1.5px solid var(--dark3)',
        background: 'var(--dark2)',
      }}>
        <img
          src={value}
          alt="Poster preview"
          style={{ width: '100%', maxHeight: 220, objectFit: 'cover', display: 'block' }}
          onError={() => { onChange(''); setUploadError('Image failed to load — try uploading again') }}
        />
        <button
          type="button"
          onClick={handleRemove}
          style={{
            position: 'absolute',
            top: 10,
            right: 10,
            background: 'rgba(9,9,9,0.82)',
            border: '1px solid rgba(239,68,68,0.4)',
            color: '#ef4444',
            fontFamily: 'var(--mono)',
            fontSize: 10,
            letterSpacing: 1,
            textTransform: 'uppercase',
            padding: '4px 12px',
            cursor: 'pointer',
            borderRadius: 4,
          }}
        >
          × Remove
        </button>
        <div style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          padding: '6px 12px',
          background: 'linear-gradient(to top, rgba(9,9,9,0.7), transparent)',
          fontFamily: 'var(--mono)',
          fontSize: 9,
          color: 'rgba(242,234,220,0.5)',
        }}>
          ✓ Uploaded to Cloudinary
        </div>
      </div>
    )
  }

  // ── Uploading (progress bar) ─────────────────────────────
  if (uploading) {
    return (
      <div style={{
        border: '2px dashed var(--orange)',
        borderRadius: 12,
        padding: '36px 24px',
        textAlign: 'center',
        background: 'rgba(212,86,26,0.03)',
      }}>
        <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)', marginBottom: 14 }}>
          Uploading… {progress}%
        </div>
        <div style={{ background: 'var(--dark3)', borderRadius: 4, height: 5, overflow: 'hidden', maxWidth: 260, margin: '0 auto' }}>
          <div style={{
            background: 'var(--orange)',
            height: '100%',
            width: `${progress}%`,
            borderRadius: 4,
            transition: 'width 0.15s ease',
          }} />
        </div>
      </div>
    )
  }

  // ── Upload area (idle) ───────────────────────────────────
  const borderColor = error || uploadError ? '#ef4444' : 'var(--dark4)'

  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        onChange={handleInputChange}
        style={{ display: 'none' }}
      />
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        style={{
          width: '100%',
          border: `2px dashed ${borderColor}`,
          borderRadius: 12,
          padding: '38px 24px',
          background: 'transparent',
          cursor: 'pointer',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 10,
          transition: 'border-color 0.15s ease, background 0.15s ease',
        }}
        onMouseOver={e => {
          if (!error && !uploadError) {
            e.currentTarget.style.borderColor = 'var(--orange)'
            e.currentTarget.style.background = 'rgba(212,86,26,0.04)'
          }
        }}
        onMouseOut={e => {
          if (!error && !uploadError) {
            e.currentTarget.style.borderColor = 'var(--dark4)'
            e.currentTarget.style.background = 'transparent'
          }
        }}
      >
        {/* Image icon */}
        <svg width={30} height={30} viewBox="0 0 24 24" fill="none"
          stroke="var(--gray2)" strokeWidth={1.4} strokeLinecap="round" strokeLinejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
          <circle cx="8.5" cy="8.5" r="1.5"/>
          <polyline points="21 15 16 10 5 21"/>
        </svg>
        <div>
          <div style={{ fontFamily: 'var(--head)', fontSize: 13, fontWeight: 600, color: 'var(--cream)', marginBottom: 5 }}>
            Click to upload poster
          </div>
          <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)' }}>
            PNG · JPG · WEBP · max 10 MB
          </div>
        </div>
      </button>
      {(uploadError || error) && (
        <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: '#ef4444', marginTop: 5 }}>
          {uploadError || error}
        </div>
      )}
    </div>
  )
}
