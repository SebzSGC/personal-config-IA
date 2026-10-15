---
titulo: Referencia API
tipo: api
estado: vigente
audiencia: [tecnico]
version_api: "{{v1}}"
url_base: "{{https://api.ejemplo.com/v1}}"
actualizado: "{{AAAA-MM-DD}}"
etiquetas: [tipo/api]
---

# 🔌 Referencia API

> [!abstract] En pocas palabras
> {{Qué se puede hacer con la API y quién la usa.}}

**URL base:** `{{url}}` · **Autenticación:** {{Bearer token en cabecera `Authorization`}}

## 📋 Resumen de endpoints

| Método | Ruta | Qué hace | Auth |
|---|---|---|---|
| `GET` | `/pedidos/{id}` | Consulta un pedido | ✅ |
| `POST` | `/pedidos` | Crea un pedido | ✅ |

---

## `POST /pedidos` · Crear pedido
{{Descripción en una frase.}}

**Cuerpo:**

| Campo | Tipo | Obligatorio | Descripción | Ejemplo |
|---|---|---|---|---|
| `cliente_id` | entero | ✅ | Cliente que pide | `87` |

**Ejemplo de petición:**
```bash
curl -X POST {{url}}/pedidos \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"cliente_id": 87, "productos": [{"id": 3, "cantidad": 2}]}'
```

**Respuesta `201 Created`:**
```json
{ "id": 1042, "estado": "creado", "total": 38500 }
```

**Errores:**

| Código | Cuándo | Qué hacer |
|---|---|---|
| `400` | Faltan campos | Revisar el cuerpo |
| `401` | Token inválido | Renovar token |

## 🔗 Relacionado
- [[Arquitectura general]] · [[Flujos y procesos]]
