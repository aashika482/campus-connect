// "Sign in with Microsoft" (the university's Microsoft 365). Shown only when the server has the
// Microsoft app's IDs (GET /auth/config). The popup returns to /msal-redirect.html; the ID token
// Microsoft gives us is checked by the backend, which signs the person in (or creates their account).
import { useState, useEffect } from 'react'
import type { IPublicClientApplication } from '@azure/msal-browser'
import { authApi, apiError } from '@/api/client'
import { useAuthStore } from '@/context/authStore'
import { useToastStore } from '@/context/toastStore'

// One per page load. Microsoft's library is large, so it's only downloaded when someone clicks the button.
let msal: Promise<IPublicClientApplication> | null = null

export function MicrosoftButton({ onSignedIn }: { onSignedIn: () => void }) {
  const { microsoft, isLoading } = useAuthStore()
  const { toast } = useToastStore()
  const [ids, setIds] = useState<{ client: string; tenant: string } | null>(null)
  useEffect(() => {
    authApi.config().then(r => {
      if (r.data.microsoft_client_id) setIds({ client: r.data.microsoft_client_id, tenant: r.data.microsoft_tenant_id })
    }).catch(() => {})
  }, [])
  if (!ids) return null

  const signIn = async () => {
    try {
      const app = msal ??= import('@azure/msal-browser').then(({ PublicClientApplication }) =>
        PublicClientApplication.createPublicClientApplication({
          auth: { clientId: ids.client, authority: `https://login.microsoftonline.com/${ids.tenant}`,
                  redirectUri: `${window.location.origin}/msal-redirect.html` },
          cache: { cacheLocation: 'sessionStorage' },
        }))
      const result = await (await app).loginPopup({ scopes: ['openid', 'profile', 'email'], prompt: 'select_account' })
      await microsoft(result.idToken)
      onSignedIn()
    } catch (err: any) {
      if (err?.errorCode === 'user_cancelled') return
      toast(apiError(err, 'Microsoft sign-in failed'), 'error')
    }
  }

  return (
    <>
      <button className="btn-g" onClick={signIn} disabled={isLoading}
        style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10 }}>
        <svg width="16" height="16" viewBox="0 0 21 21" aria-hidden="true">
          <rect x="1" y="1" width="9" height="9" fill="#F25022" /><rect x="11" y="1" width="9" height="9" fill="#7FBA00" />
          <rect x="1" y="11" width="9" height="9" fill="#00A4EF" /><rect x="11" y="11" width="9" height="9" fill="#FFB900" />
        </svg>
        Sign in with Microsoft
      </button>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, margin: '16px 0', fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)' }}>
        <div style={{ flex: 1, height: 1, background: 'var(--dark3)' }} />or<div style={{ flex: 1, height: 1, background: 'var(--dark3)' }} />
      </div>
    </>
  )
}
