from flask import Blueprint, render_template, abort
from flask_babel import _

bp = Blueprint('technologies', __name__, url_prefix='/technologies')

# Technology data with TIOBE index and details
TECHNOLOGIES = {
    'python': {
        'name': 'Python',
        'icon': 'fab fa-python',
        'color': '#3776ab',
        'tiobe_rank': 1,
        'tiobe_rating': '16.12%',
        'description': 'Python es un lenguaje de programación de alto nivel, interpretado y de propósito general. Su filosofía de diseño enfatiza la legibilidad del código con el uso de sangría significativa.',
        'description_en': 'Python is a high-level, interpreted, general-purpose programming language. Its design philosophy emphasizes code readability with the use of significant indentation.',
        'uses': [
            'Desarrollo Web (Django, Flask, FastAPI)',
            'Ciencia de Datos y Machine Learning',
            'Automatización y Scripting',
            'Inteligencia Artificial',
            'Desarrollo de APIs',
            'Procesamiento de Lenguaje Natural'
        ],
        'uses_en': [
            'Web Development (Django, Flask, FastAPI)',
            'Data Science and Machine Learning',
            'Automation and Scripting',
            'Artificial Intelligence',
            'API Development',
            'Natural Language Processing'
        ],
        'applications': [
            {'name': 'Instagram', 'desc': 'Backend desarrollado con Django'},
            {'name': 'Spotify', 'desc': 'Análisis de datos y recomendaciones'},
            {'name': 'Netflix', 'desc': 'Sistemas de recomendación'},
            {'name': 'Dropbox', 'desc': 'Cliente de escritorio'},
            {'name': 'YouTube', 'desc': 'Backend y procesamiento de video'}
        ],
        'my_experience': 'Python es mi lenguaje principal. Lo utilizo para desarrollar aplicaciones web con Flask, crear modelos de IA, automatizar procesos y construir chatbots inteligentes.',
        'my_experience_en': 'Python is my main language. I use it to develop web applications with Flask, create AI models, automate processes, and build intelligent chatbots.'
    },
    'ai-models': {
        'name': 'AI Models',
        'name_es': 'Modelos de IA',
        'icon': 'fas fa-brain',
        'color': '#ff6b6b',
        'tiobe_rank': None,
        'tiobe_rating': 'N/A (Tecnología)',
        'description': 'Los modelos de Inteligencia Artificial son sistemas computacionales diseñados para simular la inteligencia humana, capaces de aprender, razonar y tomar decisiones.',
        'description_en': 'Artificial Intelligence models are computational systems designed to simulate human intelligence, capable of learning, reasoning, and making decisions.',
        'uses': [
            'Reconocimiento de imágenes y visión por computadora',
            'Procesamiento de lenguaje natural',
            'Sistemas de recomendación',
            'Predicción y análisis predictivo',
            'Generación de contenido (GPT, DALL-E)',
            'Automatización inteligente'
        ],
        'uses_en': [
            'Image recognition and computer vision',
            'Natural language processing',
            'Recommendation systems',
            'Prediction and predictive analytics',
            'Content generation (GPT, DALL-E)',
            'Intelligent automation'
        ],
        'applications': [
            {'name': 'ChatGPT', 'desc': 'Modelo de lenguaje conversacional'},
            {'name': 'Tesla Autopilot', 'desc': 'Conducción autónoma'},
            {'name': 'Google Translate', 'desc': 'Traducción automática'},
            {'name': 'Alexa/Siri', 'desc': 'Asistentes virtuales'},
            {'name': 'GitHub Copilot', 'desc': 'Asistente de programación'}
        ],
        'my_experience': 'Implemento modelos de IA utilizando frameworks como TensorFlow, PyTorch y la API de OpenAI para crear soluciones personalizadas de clasificación, predicción y generación de contenido.',
        'my_experience_en': 'I implement AI models using frameworks like TensorFlow, PyTorch, and the OpenAI API to create custom classification, prediction, and content generation solutions.'
    },
    'nlp': {
        'name': 'NLP',
        'name_full': 'Natural Language Processing',
        'name_es': 'Procesamiento de Lenguaje Natural',
        'icon': 'fas fa-comments',
        'color': '#4ecdc4',
        'tiobe_rank': None,
        'tiobe_rating': 'N/A (Tecnología)',
        'description': 'El Procesamiento de Lenguaje Natural es una rama de la IA que permite a las computadoras entender, interpretar y generar lenguaje humano de manera significativa.',
        'description_en': 'Natural Language Processing is a branch of AI that enables computers to understand, interpret, and generate human language in a meaningful way.',
        'uses': [
            'Análisis de sentimientos',
            'Extracción de información',
            'Traducción automática',
            'Chatbots y asistentes virtuales',
            'Resumen automático de textos',
            'Clasificación de documentos'
        ],
        'uses_en': [
            'Sentiment analysis',
            'Information extraction',
            'Machine translation',
            'Chatbots and virtual assistants',
            'Automatic text summarization',
            'Document classification'
        ],
        'applications': [
            {'name': 'Google Search', 'desc': 'Comprensión de consultas'},
            {'name': 'Grammarly', 'desc': 'Corrección gramatical'},
            {'name': 'ChatGPT', 'desc': 'Generación de texto'},
            {'name': 'Duolingo', 'desc': 'Aprendizaje de idiomas'},
            {'name': 'LinkedIn', 'desc': 'Matching de empleos'}
        ],
        'my_experience': 'Utilizo técnicas de NLP con spaCy, NLTK y transformers de Hugging Face para análisis de texto, extracción de entidades y clasificación de sentimientos.',
        'my_experience_en': 'I use NLP techniques with spaCy, NLTK, and Hugging Face transformers for text analysis, entity extraction, and sentiment classification.'
    },
    'chatbots': {
        'name': 'Chatbots',
        'icon': 'fas fa-robot',
        'color': '#a55eea',
        'tiobe_rank': None,
        'tiobe_rating': 'N/A (Tecnología)',
        'description': 'Los chatbots son programas de software que simulan conversaciones humanas. Pueden ser basados en reglas o utilizar IA para proporcionar respuestas más naturales y contextuales.',
        'description_en': 'Chatbots are software programs that simulate human conversations. They can be rule-based or use AI to provide more natural and contextual responses.',
        'uses': [
            'Atención al cliente 24/7',
            'Asistentes de ventas',
            'Soporte técnico automatizado',
            'Reservaciones y agendamiento',
            'Educación y tutorías',
            'Entretenimiento interactivo'
        ],
        'uses_en': [
            '24/7 Customer service',
            'Sales assistants',
            'Automated technical support',
            'Reservations and scheduling',
            'Education and tutoring',
            'Interactive entertainment'
        ],
        'applications': [
            {'name': 'ChatGPT', 'desc': 'Chatbot conversacional avanzado'},
            {'name': 'Intercom', 'desc': 'Soporte al cliente'},
            {'name': 'Drift', 'desc': 'Ventas y marketing'},
            {'name': 'Replika', 'desc': 'Compañero de IA'},
            {'name': 'ManyChat', 'desc': 'Automatización de mensajes'}
        ],
        'my_experience': 'Desarrollo chatbots inteligentes usando LangChain, OpenAI API y Rasa. Creo asistentes conversacionales que pueden integrarse con WhatsApp, Telegram y plataformas web.',
        'my_experience_en': 'I develop intelligent chatbots using LangChain, OpenAI API, and Rasa. I create conversational assistants that can integrate with WhatsApp, Telegram, and web platforms.'
    },
    'automation': {
        'name': 'Automation',
        'name_es': 'Automatización',
        'icon': 'fas fa-cogs',
        'color': '#f39c12',
        'tiobe_rank': None,
        'tiobe_rating': 'N/A (Tecnología)',
        'description': 'La automatización de procesos implica el uso de tecnología para realizar tareas con mínima intervención humana, aumentando la eficiencia y reduciendo errores.',
        'description_en': 'Process automation involves using technology to perform tasks with minimal human intervention, increasing efficiency and reducing errors.',
        'uses': [
            'Web scraping y extracción de datos',
            'Automatización de tareas repetitivas',
            'CI/CD pipelines',
            'Testing automatizado',
            'Procesamiento de documentos',
            'Integración de sistemas'
        ],
        'uses_en': [
            'Web scraping and data extraction',
            'Repetitive task automation',
            'CI/CD pipelines',
            'Automated testing',
            'Document processing',
            'System integration'
        ],
        'applications': [
            {'name': 'Zapier', 'desc': 'Automatización de workflows'},
            {'name': 'UiPath', 'desc': 'RPA empresarial'},
            {'name': 'GitHub Actions', 'desc': 'CI/CD automatizado'},
            {'name': 'Selenium', 'desc': 'Testing web automatizado'},
            {'name': 'Apache Airflow', 'desc': 'Orquestación de datos'}
        ],
        'my_experience': 'Creo scripts de automatización con Python, Selenium y APIs. Desarrollo pipelines de datos, bots de scraping y sistemas de integración que ahorran horas de trabajo manual.',
        'my_experience_en': 'I create automation scripts with Python, Selenium, and APIs. I develop data pipelines, scraping bots, and integration systems that save hours of manual work.'
    },
    'flask': {
        'name': 'Flask',
        'icon': 'fas fa-flask',
        'color': '#000000',
        'tiobe_rank': None,
        'tiobe_rating': 'Framework Python',
        'description': 'Flask es un microframework web de Python que proporciona las herramientas básicas para crear aplicaciones web, manteniendo un núcleo simple y extensible.',
        'description_en': 'Flask is a Python web microframework that provides the basic tools to create web applications while maintaining a simple and extensible core.',
        'uses': [
            'APIs RESTful',
            'Aplicaciones web',
            'Microservicios',
            'Prototipos rápidos',
            'Dashboards y paneles',
            'Backend para aplicaciones móviles'
        ],
        'uses_en': [
            'RESTful APIs',
            'Web applications',
            'Microservices',
            'Rapid prototypes',
            'Dashboards and panels',
            'Backend for mobile apps'
        ],
        'applications': [
            {'name': 'Netflix', 'desc': 'Microservicios internos'},
            {'name': 'Reddit', 'desc': 'Algunas funcionalidades'},
            {'name': 'Lyft', 'desc': 'APIs de servicios'},
            {'name': 'Pinterest', 'desc': 'Partes del backend'},
            {'name': 'LinkedIn', 'desc': 'Servicios internos'}
        ],
        'my_experience': 'Flask es mi framework preferido para desarrollo web. Esta misma página está construida con Flask. Lo uso para crear APIs, aplicaciones full-stack y microservicios.',
        'my_experience_en': 'Flask is my preferred framework for web development. This very page is built with Flask. I use it to create APIs, full-stack applications, and microservices.'
    },
    'langchain': {
        'name': 'LangChain',
        'icon': 'fas fa-link',
        'color': '#1a5f2a',
        'tiobe_rank': None,
        'tiobe_rating': 'Framework IA',
        'description': 'LangChain es un framework para desarrollar aplicaciones potenciadas por modelos de lenguaje. Permite crear cadenas complejas de procesamiento de lenguaje natural.',
        'description_en': 'LangChain is a framework for developing applications powered by language models. It allows creating complex natural language processing chains.',
        'uses': [
            'Chatbots con memoria y contexto',
            'Agentes autónomos de IA',
            'RAG (Retrieval Augmented Generation)',
            'Procesamiento de documentos',
            'Integración con bases de datos vectoriales',
            'Aplicaciones conversacionales avanzadas'
        ],
        'uses_en': [
            'Chatbots with memory and context',
            'Autonomous AI agents',
            'RAG (Retrieval Augmented Generation)',
            'Document processing',
            'Vector database integration',
            'Advanced conversational applications'
        ],
        'applications': [
            {'name': 'Notion AI', 'desc': 'Asistente de documentos'},
            {'name': 'Jasper', 'desc': 'Generación de contenido'},
            {'name': 'Copy.ai', 'desc': 'Marketing automatizado'},
            {'name': 'Custom Chatbots', 'desc': 'Empresas Fortune 500'},
            {'name': 'Document QA', 'desc': 'Sistemas de preguntas'}
        ],
        'my_experience': 'Utilizo LangChain para crear chatbots inteligentes con memoria, sistemas RAG que consultan documentos, y agentes autónomos que pueden ejecutar tareas complejas.',
        'my_experience_en': 'I use LangChain to create intelligent chatbots with memory, RAG systems that query documents, and autonomous agents that can execute complex tasks.'
    },
    'openai-api': {
        'name': 'OpenAI API',
        'icon': 'fas fa-microchip',
        'color': '#412991',
        'tiobe_rank': None,
        'tiobe_rating': 'API de IA',
        'description': 'La API de OpenAI proporciona acceso a modelos de IA avanzados como GPT-4, DALL-E y Whisper para generar texto, imágenes y transcribir audio.',
        'description_en': 'The OpenAI API provides access to advanced AI models like GPT-4, DALL-E, and Whisper to generate text, images, and transcribe audio.',
        'uses': [
            'Generación de texto y contenido',
            'Chatbots conversacionales',
            'Análisis de sentimientos',
            'Traducción automática',
            'Generación de código',
            'Transcripción de audio'
        ],
        'uses_en': [
            'Text and content generation',
            'Conversational chatbots',
            'Sentiment analysis',
            'Machine translation',
            'Code generation',
            'Audio transcription'
        ],
        'applications': [
            {'name': 'ChatGPT', 'desc': 'Chatbot conversacional'},
            {'name': 'GitHub Copilot', 'desc': 'Asistente de código'},
            {'name': 'Duolingo', 'desc': 'Roleplay de idiomas'},
            {'name': 'Canva', 'desc': 'Magic Write'},
            {'name': 'Stripe', 'desc': 'Documentación automática'}
        ],
        'my_experience': 'Integro la API de OpenAI en mis proyectos para crear chatbots, generar contenido, analizar textos y construir asistentes virtuales personalizados.',
        'my_experience_en': 'I integrate the OpenAI API in my projects to create chatbots, generate content, analyze texts, and build custom virtual assistants.'
    },
    'docker': {
        'name': 'Docker',
        'icon': 'fab fa-docker',
        'color': '#2496ed',
        'tiobe_rank': None,
        'tiobe_rating': 'Plataforma DevOps',
        'description': 'Docker es una plataforma de contenedorización que permite empaquetar aplicaciones con todas sus dependencias para garantizar que funcionen de manera consistente en cualquier entorno.',
        'description_en': 'Docker is a containerization platform that allows packaging applications with all their dependencies to ensure they work consistently in any environment.',
        'uses': [
            'Contenedorización de aplicaciones',
            'Desarrollo local consistente',
            'CI/CD pipelines',
            'Microservicios',
            'Despliegue en la nube',
            'Aislamiento de entornos'
        ],
        'uses_en': [
            'Application containerization',
            'Consistent local development',
            'CI/CD pipelines',
            'Microservices',
            'Cloud deployment',
            'Environment isolation'
        ],
        'applications': [
            {'name': 'Spotify', 'desc': 'Microservicios'},
            {'name': 'PayPal', 'desc': 'Infraestructura de contenedores'},
            {'name': 'ADP', 'desc': 'Modernización de apps'},
            {'name': 'Expedia', 'desc': 'Despliegue automatizado'},
            {'name': 'BBC', 'desc': 'Streaming de contenido'}
        ],
        'my_experience': 'Uso Docker para contenerizar todas mis aplicaciones. Esta página web corre en contenedores Docker con Nginx, Flask y PostgreSQL orquestados con Docker Compose.',
        'my_experience_en': 'I use Docker to containerize all my applications. This website runs in Docker containers with Nginx, Flask, and PostgreSQL orchestrated with Docker Compose.'
    },
    'postgresql': {
        'name': 'PostgreSQL',
        'icon': 'fas fa-database',
        'color': '#336791',
        'tiobe_rank': None,
        'tiobe_rating': '#1 en DB-Engines',
        'description': 'PostgreSQL es un sistema de gestión de bases de datos relacional de código abierto, conocido por su robustez, extensibilidad y cumplimiento de estándares SQL.',
        'description_en': 'PostgreSQL is an open-source relational database management system known for its robustness, extensibility, and SQL standards compliance.',
        'uses': [
            'Bases de datos empresariales',
            'Aplicaciones web',
            'Data warehousing',
            'Sistemas geoespaciales (PostGIS)',
            'Análisis de datos',
            'Aplicaciones de alta disponibilidad'
        ],
        'uses_en': [
            'Enterprise databases',
            'Web applications',
            'Data warehousing',
            'Geospatial systems (PostGIS)',
            'Data analytics',
            'High availability applications'
        ],
        'applications': [
            {'name': 'Instagram', 'desc': 'Base de datos principal'},
            {'name': 'Spotify', 'desc': 'Almacenamiento de datos'},
            {'name': 'Reddit', 'desc': 'Backend de datos'},
            {'name': 'Twitch', 'desc': 'Datos de usuarios'},
            {'name': 'Apple', 'desc': 'Servicios internos'}
        ],
        'my_experience': 'PostgreSQL es mi base de datos preferida. La utilizo con SQLAlchemy en todos mis proyectos Flask por su potencia, confiabilidad y excelente soporte para JSON.',
        'my_experience_en': 'PostgreSQL is my preferred database. I use it with SQLAlchemy in all my Flask projects for its power, reliability, and excellent JSON support.'
    },
    'javascript': {
        'name': 'JavaScript',
        'icon': 'fab fa-js',
        'color': '#f7df1e',
        'tiobe_rank': 6,
        'tiobe_rating': '3.19%',
        'description': 'JavaScript es un lenguaje de programación interpretado que se utiliza principalmente para crear contenido web interactivo. Es el lenguaje de la web.',
        'description_en': 'JavaScript is an interpreted programming language primarily used to create interactive web content. It is the language of the web.',
        'uses': [
            'Desarrollo frontend (React, Vue, Angular)',
            'Backend (Node.js)',
            'Aplicaciones móviles (React Native)',
            'Desarrollo de APIs',
            'Automatización de navegadores',
            'Aplicaciones de escritorio (Electron)'
        ],
        'uses_en': [
            'Frontend development (React, Vue, Angular)',
            'Backend (Node.js)',
            'Mobile applications (React Native)',
            'API development',
            'Browser automation',
            'Desktop applications (Electron)'
        ],
        'applications': [
            {'name': 'Facebook', 'desc': 'React frontend'},
            {'name': 'Netflix', 'desc': 'Interfaz de usuario'},
            {'name': 'Uber', 'desc': 'App móvil y web'},
            {'name': 'PayPal', 'desc': 'Node.js backend'},
            {'name': 'LinkedIn', 'desc': 'Frontend interactivo'}
        ],
        'my_experience': 'Uso JavaScript para crear interfaces interactivas, animaciones y funcionalidades del lado del cliente. También lo utilizo con Node.js para scripts de automatización.',
        'my_experience_en': 'I use JavaScript to create interactive interfaces, animations, and client-side functionalities. I also use it with Node.js for automation scripts.'
    },
    'git': {
        'name': 'Git',
        'icon': 'fab fa-git-alt',
        'color': '#f05032',
        'tiobe_rank': None,
        'tiobe_rating': '#1 Control de Versiones',
        'description': 'Git es un sistema de control de versiones distribuido que permite rastrear cambios en el código fuente durante el desarrollo de software.',
        'description_en': 'Git is a distributed version control system that allows tracking changes in source code during software development.',
        'uses': [
            'Control de versiones de código',
            'Colaboración en equipos',
            'CI/CD pipelines',
            'Gestión de releases',
            'Code review',
            'Backup de proyectos'
        ],
        'uses_en': [
            'Code version control',
            'Team collaboration',
            'CI/CD pipelines',
            'Release management',
            'Code review',
            'Project backup'
        ],
        'applications': [
            {'name': 'GitHub', 'desc': 'Plataforma de hosting'},
            {'name': 'GitLab', 'desc': 'DevOps completo'},
            {'name': 'Bitbucket', 'desc': 'Integración Atlassian'},
            {'name': 'Linux Kernel', 'desc': 'Creado para esto'},
            {'name': 'Todas las empresas tech', 'desc': 'Estándar de la industria'}
        ],
        'my_experience': 'Git es fundamental en mi flujo de trabajo. Uso GitHub para todos mis proyectos, manejo branches, pull requests y integración continua con GitHub Actions.',
        'my_experience_en': 'Git is fundamental in my workflow. I use GitHub for all my projects, managing branches, pull requests, and continuous integration with GitHub Actions.'
    }
}


@bp.route('/')
def index():
    """List all technologies"""
    return render_template('technologies/index.html', technologies=TECHNOLOGIES)


@bp.route('/<slug>')
def detail(slug):
    """Show technology details"""
    if slug not in TECHNOLOGIES:
        abort(404)
    
    tech = TECHNOLOGIES[slug]
    tech['slug'] = slug
    return render_template('technologies/detail.html', tech=tech, all_technologies=TECHNOLOGIES)
