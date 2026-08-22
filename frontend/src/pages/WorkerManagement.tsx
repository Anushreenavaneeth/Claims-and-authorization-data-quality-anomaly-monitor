import { useState, useEffect, FormEvent } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import api from "../services/api";
import { UserPlus, Trash2, Loader2, CheckCircle2, AlertCircle, Eye, EyeOff, Users } from "lucide-react";

interface Worker {
  id: string;
  name: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export default function WorkerManagement() {
  const [workers,  setWorkers]  = useState<Worker[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [creating, setCreating] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [success,  setSuccess]  = useState("");
  const [error,    setError]    = useState("");
  const [showPass, setShowPass] = useState(false);
  const [form,     setForm]     = useState({ name: "", email: "", password: "" });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  const fetchWorkers = async () => {
    try {
      const res = await api.get("/admin/workers");
      setWorkers(res.data);
    } catch {
      setError("Failed to load workers.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchWorkers(); }, []);

  const validate = () => {
    const e: Record<string, string> = {};
    if (!form.name.trim())  e.name     = "Name is required.";
    if (!form.email.trim()) e.email    = "Email is required.";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = "Enter a valid email.";
    if (!form.password)     e.password = "Password is required.";
    else if (form.password.length < 8) e.password = "Minimum 8 characters.";
    return e;
  };

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    const errs = validate();
    setFormErrors(errs);
    if (Object.keys(errs).length) return;
    setCreating(true);
    setError(""); setSuccess("");
    try {
      await api.post("/admin/workers", form);
      setSuccess(`Worker "${form.name}" created successfully.`);
      setForm({ name: "", email: "", password: "" });
      setShowForm(false);
      fetchWorkers();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg ?? "Failed to create worker.");
    } finally {
      setCreating(false);
    }
  };

  const handleDeactivate = async (id: string, name: string) => {
    if (!confirm(`Deactivate worker "${name}"?`)) return;
    try {
      await api.patch(`/admin/workers/${id}/deactivate`);
      fetchWorkers();
    } catch { setError("Failed to deactivate worker."); }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Worker Management</h1>
          <p className="text-muted-foreground mt-1">Manage analyst and worker accounts</p>
        </div>
        <Button
          onClick={() => { setShowForm(s => !s); setError(""); setSuccess(""); setFormErrors({}); }}
        >
          <UserPlus className="h-4 w-4 mr-2" />
          {showForm ? "Cancel" : "New Worker"}
        </Button>
      </div>

      {/* Feedback */}
      {success && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-green-50 border border-green-200 text-sm text-green-700">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />{success}
        </div>
      )}
      {error && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />{error}
        </div>
      )}

      {/* Create worker form */}
      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Create New Worker Account</CardTitle>
            <CardDescription>The worker will be able to log in and manage assigned tasks</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} noValidate>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
                {/* Name */}
                <div>
                  <label className="block text-sm font-medium mb-1">Full Name</label>
                  <Input
                    value={form.name}
                    onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                    placeholder="Full name"
                    className={formErrors.name ? "border-red-400" : ""}
                  />
                  {formErrors.name && <p className="mt-1 text-xs text-red-600">{formErrors.name}</p>}
                </div>
                {/* Email */}
                <div>
                  <label className="block text-sm font-medium mb-1">Email Address</label>
                  <Input
                    type="email"
                    value={form.email}
                    onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
                    placeholder="worker@org.com"
                    className={formErrors.email ? "border-red-400" : ""}
                  />
                  {formErrors.email && <p className="mt-1 text-xs text-red-600">{formErrors.email}</p>}
                </div>
                {/* Password */}
                <div>
                  <label className="block text-sm font-medium mb-1">Password</label>
                  <div className="relative">
                    <Input
                      type={showPass ? "text" : "password"}
                      value={form.password}
                      onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                      placeholder="Min 8 characters"
                      className={formErrors.password ? "border-red-400 pr-10" : "pr-10"}
                    />
                    <button type="button" onClick={() => setShowPass(s => !s)}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                      {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  {formErrors.password && <p className="mt-1 text-xs text-red-600">{formErrors.password}</p>}
                </div>
              </div>
              <Button type="submit" disabled={creating}>
                {creating
                  ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Creating…</>
                  : <><UserPlus className="h-4 w-4 mr-2" />Create Worker</>}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Workers table */}
      <Card>
        <CardHeader>
          <CardTitle>All Workers</CardTitle>
          <CardDescription>
            {loading ? "Loading…" : `${workers.length} worker${workers.length !== 1 ? "s" : ""} registered`}
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="w-6 h-6 text-muted-foreground animate-spin" />
            </div>
          ) : workers.length === 0 ? (
            <div className="text-center py-16">
              <Users className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
              <p className="text-sm text-muted-foreground">No workers yet.</p>
              <p className="text-xs text-muted-foreground mt-1">Click "New Worker" to add the first one.</p>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  {["Name", "Email", "Status", "Created", ""].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {workers.map((w) => (
                  <tr key={w.id} className="border-b hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-full bg-blue-100 border border-blue-200 flex items-center justify-center text-xs font-bold text-blue-700 flex-shrink-0">
                          {w.name.charAt(0).toUpperCase()}
                        </div>
                        <span className="font-medium">{w.name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">{w.email}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${
                        w.is_active
                          ? "bg-green-50 text-green-700 border-green-200"
                          : "bg-gray-100 text-gray-500 border-gray-200"
                      }`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${w.is_active ? "bg-green-500" : "bg-gray-400"}`} />
                        {w.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">
                      {new Date(w.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {w.is_active && (
                        <button
                          onClick={() => handleDeactivate(w.id, w.name)}
                          className="p-1.5 rounded-md text-muted-foreground hover:text-red-600 hover:bg-red-50 transition-colors"
                          aria-label={`Deactivate ${w.name}`}
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
