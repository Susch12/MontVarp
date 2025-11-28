# Sistema Distribuido de Simulación Monte Carlo con Paso de Mensajes

##  Tabla de Contenidos

1.  [Descripción General](https://www.google.com/search?q=%23descripci%C3%B3n-general)
2.  [Requisitos del Sistema](https://www.google.com/search?q=%23requisitos-del-sistema)
3.  [Arquitectura del Sistema](https://www.google.com/search?q=%23arquitectura-del-sistema)
4.  [Especificación del Archivo de Modelo](https://www.google.com/search?q=%23especificaci%C3%B3n-del-archivo-de-modelo)
5.  [Componentes del Sistema](https://www.google.com/search?q=%23componentes-del-sistema)
6.  [Stack Tecnológico](https://www.google.com/search?q=%23stack-tecnol%C3%B3gico)
7.  [Ejemplos de Modelos](https://www.google.com/search?q=%23ejemplos-de-modelos)
8.  **Ejecución y Despliegue**
9.  **Flujo de Ejecución**

-----

## 1\. Descripción General

Este sistema implementa una **simulación Monte Carlo distribuida** utilizando el **modelo de paso de mensajes** a través de RabbitMQ.

### Características Principales

  *  **Productor único**: Genera escenarios únicos y publica la definición del modelo.
  *  **Modelo Flexible (INI)**: Soporte para funciones definidas como **expresiones matemáticas seguras** o **código Python** restringido.
  *  **Variables Estocásticas**: Soporte para **6 distribuciones de probabilidad** (Normal, Uniforme, Exponencial, Lognormal, Triangular, Binomial).
  *  **Procesamiento Distribuido**: Múltiples consumidores escalables que ejecutan el modelo en paralelo.
  *  **Robustez (DLQ)**: Manejo avanzado de fallos con **reintentos automáticos** y redireccionamiento a **Dead Letter Queues (DLQ)** para mensajes irrecuperables.
  *  **Visualización en Tiempo Real**: Dashboard web con estadísticas detalladas, análisis de **convergencia** y **tests de normalidad**.
  *  **Exportación de Datos**: Funcionalidad de exportación de resultados y estadísticas a formatos **JSON y CSV**.

-----

## 2\. Requisitos del Sistema

### Requisitos Funcionales

1.  **Productor**: Lee el archivo `.ini`, genera escenarios basados en las 6 distribuciones y publica el modelo purgando la cola anterior.
2.  **Consumidores**: Leen el modelo una sola vez, ejecutan la función (expresión o código Python) de forma segura y publican resultados en `cola_resultados`.
3.  **Manejo de Errores**: Los consumidores aplican hasta **3 reintentos** a mensajes con errores recuperables. Errores no recuperables (`TimeoutException`, `SecurityException`) se envían directamente a la DLQ.
4.  **Dashboard**: Muestra progreso, estadísticas descriptivas, **tests de normalidad (Kolmogorov-Smirnov, Shapiro-Wilk)**, análisis de **convergencia de media y varianza** y permite la exportación de datos.

-----

## 3\. Arquitectura del Sistema

El sistema se basa en 4 componentes principales orquestados por Docker Compose: **RabbitMQ**, **Producer**, **Consumer** (escalable) y **Dashboard**.

### Políticas de Colas en RabbitMQ

| Nombre de Cola | Propósito | Durabilidad | Configuración Clave |
| :--- | :--- | :--- | :--- |
| `cola_modelo` | Definición del modelo | Persistente | `x-max-length`: 1 (Se purga al publicar nuevo modelo) |
| `cola_escenarios` | Escenarios a procesar | Persistente | **DLQ** configurada a `cola_dlq_escenarios` |
| `cola_resultados` | Resultados de ejecución | Persistente | **DLQ** configurada a `cola_dlq_resultados` |
| `cola_stats_productor` | Estadísticas del productor | No Persistente | **TTL**: 60s |
| `cola_stats_consumidores` | Estadísticas de consumidores | No Persistente | **TTL**: 60s |

-----

## 4\. Especificación del Archivo de Modelo

El modelo se define en un archivo con formato **INI** y cuatro secciones principales: `[METADATA]`, `[VARIABLES]`, `[FUNCION]` y `[SIMULACION]`.

### [VARIABLES]

Define las variables estocásticas y sus distribuciones:

| Distribución | Tipo de Variable | Parámetros Requeridos |
| :--- | :--- | :--- |
| `normal` | `float` | `media`, `std` |
| `uniform` | `float` | `min`, `max` |
| `exponential` | `float` | `lambda` o `scale` |
| `lognormal` | `float` | `mu`, `sigma` |
| `triangular` | `float` | `left`, `mode`, `right` |
| `binomial` | `int` | `n`, `p` |

### [FUNCION]

Soporta dos tipos de funciones:

| Tipo | Detalle de Implementación | Seguridad |
| :--- | :--- | :--- |
| `tipo = expresion` | Expresión matemática de una sola línea (ej. `x + y**2`). | Evaluada mediante **AST (Abstract Syntax Tree)**, permitiendo solo operaciones matemáticas seguras. |
| `tipo = codigo` | Bloque de código Python multilínea. Debe definir una variable `resultado`. | Ejecutado en un sandbox seguro con **RestrictedPython** y un **timeout** para evitar código malicioso o bucles infinitos. |

-----

## 5\. Componentes del Sistema

### Productor (`src/producer/producer.py`)

Se encarga de la orquestación inicial de la simulación. Utiliza el `ModelParser` para leer el modelo y el `DistributionGenerator` para crear los valores aleatorios de cada escenario.

### Consumidor (`src/consumer/consumer.py`)

Procesa los escenarios. Si el modelo es de tipo `expresion`, utiliza `SafeExpressionEvaluator`. Si es de tipo `codigo`, utiliza `PythonExecutor` (RestrictedPython). La implementación incluye manejo avanzado de errores, con seguimiento de reintentos y errores por tipo.

### Dashboard (`src/dashboard/app.py` y `src/dashboard/data_manager.py`)

Utiliza Dash y Plotly para la visualización. El `DataManager` consume colas de estadísticas en un *thread* separado y realiza en memoria el análisis avanzado:

  * **Estadísticas Descriptivas**: Cálculo de media, desviación estándar, percentiles, e intervalo de confianza del 95%.
  * **Convergencia**: Gráficas de la media y varianza acumuladas versus el número de escenarios (`n`).
  * **Normalidad**: Aplicación de tests de **Kolmogorov-Smirnov** y **Shapiro-Wilk** a los resultados.

-----

## 6\. Stack Tecnológico

| Componente | Tecnología | Versión Mínima | Propósito |
| :--- | :--- | :--- | :--- |
| Lenguaje | **Python** | 3.10+ | Lógica de negocio |
| Message Broker | **RabbitMQ** | 3.12+ | Comunicación asíncrona |
| Cliente Mensajería | **Pika** | 1.3+ | Cliente AMQP |
| Estadística/Simulación | **NumPy, SciPy** | 1.24+, 1.10+ | Generación de distribuciones y análisis |
| Dashboard | **Dash, Plotly** | 2.10+, 5.14+ | Visualización interactiva en tiempo real |
| Seguridad/Ejecución | **RestrictedPython** | 6.0 | Sandbox para código Python |
| Utilidades | **Pandas** | 2.0+ | Exportación a CSV |

-----

## 7\. Ejemplos de Modelos

Los siguientes modelos de ejemplo se encuentran en la carpeta `modelos/` y demuestran las capacidades del sistema:

1.  **`ejemplo_simple.ini`**: Modelo básico de suma de dos variables normales, utilizando `tipo = expresion`.
2.  **`ejemplo_codigo_python.ini`**: Cálculo de distancia euclidiana y ángulo polar, mostrando el uso de `tipo = codigo` e importando el módulo `math`.
3.  **`ejemplo_funcion_simple.ini`**: Uso de `tipo = codigo` para definir y llamar a funciones auxiliares (con `def`) dentro del código del modelo.
4.  **`ejemplo_6_distribuciones.ini`**: Análisis de riesgo financiero complejo que utiliza las **6 distribuciones de probabilidad** soportadas y `tipo = codigo`.
5.  **`ejemplo_complejo_negocio.ini`**: Simulación completa de viabilidad de proyecto de negocio, usando todas las capacidades (6 distribuciones, funciones auxiliares, lógica de negocio).

-----

## 8\. Ejecución y Despliegue

El sistema está completamente dockerizado y la forma más simple de ejecutar todos los servicios es mediante `docker-compose` y los *scripts* de automatización.

###  Quick Start (Usando `start.sh`)

1.  **Configuración Inicial**:
    ```bash
    # Copiar .env.example a .env
    cp .env.example .env
    # Opcional: Editar .env para ajustar el MODELO_FILE o DEFAULT_NUM_ESCENARIOS
    ```
2.  **Iniciar el Sistema (y construir imágenes si es la primera vez)**:
    ```bash
    # Inicia todos los servicios con 1 consumidor
    ./start.sh --build

    # Inicia con 5 consumidores (escalabilidad)
    ./start.sh --build 5
    ```
3.  **Acceso a URLs**:
      * **Dashboard de Monitoreo**: `http://localhost:8050`
      * **RabbitMQ Management UI**: `http://localhost:15672` (Usuario: `admin`, Password: `password`)
4.  **Verificar Logs**:
    ```bash
    docker-compose logs -f
    ```
5.  **Detener y Limpiar**:
    ```bash
    # Detener servicios (mantiene volumes de RabbitMQ)
    ./stop.sh

    # Detener y eliminar volumes (limpieza total de datos)
    ./stop.sh --clean
    ```

###  Escalabilidad

El servicio **Consumer** está diseñado para ser escalable horizontalmente, lo cual se maneja directamente con `docker-compose` a través del *script* `start.sh`:

```bash
# Escalar a 5 consumidores
docker-compose up -d --scale consumer=5

# O usando el script:
./start.sh 5
```

-----

## 9\. Flujo de Ejecución

El flujo de trabajo es completamente asíncrono y se coordina a través del broker RabbitMQ.

### Secuencia de Mensajes y Procesos

| Paso | Componente | Acción | Cola de Interacción | Resultado/Siguiente Paso |
| :--- | :--- | :--- | :--- | :--- |
| **1.** | **Producer** | Lee, valida y compila el modelo. **Purga** `cola_modelo` para invalidar versiones anteriores. | `cola_modelo` | El modelo se publica en `cola_modelo`. |
| **2.** | **Consumer (N)** | Al iniciar, cada consumidor lee el modelo desde la cola. | `cola_modelo` | El consumidor inicializa su `PythonExecutor` o `SafeExpressionEvaluator`. |
| **3.** | **Producer** | Genera **N** escenarios únicos basados en las distribuciones y los publica de forma persistente. | `cola_escenarios` | Los escenarios esperan en la cola para ser procesados (FIFO). |
| **4.** | **Producer** | Publica métricas de progreso (tasa, ETA, generados). | `cola_stats_productor` | El Dashboard consume esta información en tiempo real. |
| **5.** | **Consumer (N)** | Consume un escenario de la cola. | `cola_escenarios` | El consumidor ejecuta la función del modelo. |
| **6.** | **Consumer (N)** | Si la ejecución es exitosa, el resultado se publica. | `cola_resultados` | El resultado está disponible para análisis. |
| **7.** | **Consumer (N)** | Publica métricas de desempeño (tasa, errores, reintentos). | `cola_stats_consumidores` | El Dashboard consume y actualiza la tabla de consumidores. |
| **8.** | **Dashboard** | Consume resultados y estadísticas en tiempo real. | `cola_resultados`, `cola_stats_...` | Actualización de gráficas de progreso, tasas y análisis de resultados/convergencia. |
| **9.** | **Consumer (N)** | Si la ejecución **falla** con error recuperable, el mensaje se republica con el contador de reintentos incrementado. | `cola_escenarios` | El mensaje reintenta ser procesado (máx. 3 veces). |
| **10.** | **Consumer (N)** | Si la ejecución **falla** con error no recuperable (o excede reintentos), el mensaje se envía a la DLQ. | `cola_dlq_escenarios` | El mensaje fallido está aislado y no bloquea la simulación. |
