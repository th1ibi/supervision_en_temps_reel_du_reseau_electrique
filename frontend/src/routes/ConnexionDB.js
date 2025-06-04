import { useState } from "react";
import stegLogo from "../assets/steg.png";
import { Eye, EyeOff } from "lucide-react"; // Icônes

export default function ConnexionDB({ onSuccess }) {
  const [formData, setFormData] = useState({
    dbname: "",
    password: "",
    user: "postgres",
    host: "localhost",
    port: "5432",
  });

  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e) =>
    setFormData({ ...formData, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/api/connect-db", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (data.status === "connected") {
        onSuccess();
      } else {
        setError(data.detail || "Échec de la connexion.");
      }
    } catch (err) {
      console.error("Erreur lors de la connexion :", err);
      setError("Erreur réseau ou serveur injoignable.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: "20px", maxWidth: "400px", margin: "auto" }}>
      {/* Logo STEG centré */}
      <div style={{ textAlign: "center", marginBottom: "30px" }}>
        <img src={stegLogo} alt="Logo STEG" style={{ height: "100px" }} />
      </div>

      <form onSubmit={handleSubmit} style={{ display: "grid", gap: "20px" }}>
        <div>
          <label className="block font-bold">Nom de la base</label>
          <input
            name="dbname"
            value={formData.dbname}
            onChange={handleChange}
            required
            className="w-full border px-4 py-2 rounded"
            style={{ width: "100%", padding: "8px" }}
          />
        </div>

        <div>
          <label className="block font-bold">Mot de passe</label>
          <div style={{ position: "relative" }}>
            <input
              type={showPassword ? "text" : "password"}
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              className="w-full border px-4 py-2 rounded"
              style={{ width: "100%", padding: "8px", paddingRight: "40px" }}
            />
            <div
              onClick={() => setShowPassword(!showPassword)}
              style={{
                position: "absolute",
                top: "50%",
                right: "10px",
                transform: "translateY(-50%)",
                cursor: "pointer",
              }}
            >
              {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
            </div>
          </div>
        </div>

        {error && <div style={{ color: "red" }}>{error}</div>}

        <button
          type="submit"
          disabled={loading}
          style={{
            backgroundColor: "#007bff",
            color: "white",
            padding: "12px",
            fontWeight: "bold",
            border: "none",
            borderRadius: "5px",
            cursor: "pointer",
            marginTop: "10px",
          }}
        >
          {loading ? "Connexion..." : "Se connecter"}
        </button>
      </form>
    </div>
  );
}
