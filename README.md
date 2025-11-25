# Netflame Estufa - Home Assistant Integration

Integración de Home Assistant para controlar estufas de pellets Netflame.

## Características

- Control de encendido/apagado
- Lectura de temperatura
- Control de potencia (niveles 1-9)
- Lectura de alarmas
- Entity climático para modo HVAC y presets de potencia
- Sensores para temperatura y alarmas

## Instalación

### Vía HACS

1. Abre HACS en tu instancia de Home Assistant
2. Ve a "Integraciones"
3. Busca "Netflame Estufa"
4. Instala la integración
5. Reinicia Home Assistant

### Instalación manual

1. Clona este repositorio en tu carpeta `custom_components`:
```bash
git clone https://github.com/evaristocuesta/netflame-homeassistant-integration.git ~/.homeassistant/custom_components/netflame
```

2. Reinicia Home Assistant

## Configuración

Necesitarás proporcionar:
- **Serial**: Número de serie de tu estufa Netflame
- **Contraseña**: Contraseña de acceso a la estufa

## Requisitos

- Home Assistant 2024.1.0 o superior
- Conexión a Internet (la estufa se comunica con servidores en la nube)

## Codeowners

- [@evaristocuesta](https://github.com/evaristocuesta)

## Reporte de problemas

Si encuentras problemas, por favor abre un issue en el [rastreador de problemas](https://github.com/evaristocuesta/netflame-homeassistant-integration/issues)
