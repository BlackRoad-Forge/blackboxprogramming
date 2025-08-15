export class PSSHAInfinityClient {
  constructor(private baseUrl: string, private token: string) {}
  private h(extra: Record<string,string> = {}) {
    return { "Authorization": `Bearer ${this.token}`, "Content-Type":"application/json", ...extra };
  }
  async health() {
    const r = await fetch(`${this.baseUrl}/health`);
    return r.json();
  }
  async hash(payload: any, breath=0, stages?: string[], meta?: any, salt?: string) {
    const r = await fetch(`${this.baseUrl}/hash`, { method: "POST", headers: this.h(), body: JSON.stringify({payload, breath, stages, meta, salt}) });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  }
  async verify(hash_hex: string, signature_hex: string) {
    const r = await fetch(`${this.baseUrl}/verify`, { method: "POST", headers: this.h(), body: JSON.stringify({hash_hex, signature_hex}) });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  }
  async chatBind(message: string, context: any, breath=0, meta?: any, idemKey?: string) {
    const headers: any = this.h();
    if (idemKey) headers["Idempotency-Key"] = idemKey;
    const r = await fetch(`${this.baseUrl}/chat-bind`, { method: "POST", headers, body: JSON.stringify({message, context, breath, meta}) });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  }
}
