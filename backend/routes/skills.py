from fastapi import APIRouter, Depends
from middleware.auth import get_current_user

router = APIRouter(prefix="/api/skills", tags=["Skills"])

SKILLS = [
    # Tech
    "Python","JavaScript","TypeScript","Java","Kotlin","Swift","Go","Rust","C++","C#","PHP","Ruby","Scala",
    "React","React Native","Vue.js","Angular","Next.js","Nuxt.js","Svelte","Flutter","Expo",
    "Node.js","Express.js","FastAPI","Django","Flask","Spring Boot","Laravel","Rails",
    "MongoDB","PostgreSQL","MySQL","Redis","Firebase","DynamoDB","Cassandra","Elasticsearch",
    "AWS","Azure","GCP","Docker","Kubernetes","Terraform","CI/CD","Jenkins","GitHub Actions",
    "REST API","GraphQL","WebSockets","gRPC","Microservices","System Design",
    "Machine Learning","Deep Learning","NLP","Computer Vision","TensorFlow","PyTorch","Scikit-learn",
    "Pandas","NumPy","Data Analysis","Power BI","Tableau","SQL","Spark","Hadoop",
    "Git","Linux","Bash","Nginx","Apache","Webpack","Vite",
    "HTML","CSS","Tailwind CSS","Bootstrap","SASS","Figma","Adobe XD",
    "iOS Development","Android Development","Cross-platform Development",
    "Blockchain","Solidity","Web3","Smart Contracts",
    "Cybersecurity","Penetration Testing","Network Security","OWASP",
    "Agile","Scrum","Kanban","JIRA","Confluence","Notion",
    "Unit Testing","Jest","Pytest","Selenium","Cypress","Postman",
    # Non-tech
    "Product Management","Project Management","Business Analysis","Stakeholder Management",
    "Digital Marketing","SEO","SEM","Content Marketing","Social Media Marketing","Email Marketing",
    "Sales","Business Development","CRM","Salesforce","HubSpot",
    "UI/UX Design","Wireframing","Prototyping","User Research","Usability Testing",
    "Financial Analysis","Accounting","Budgeting","Excel","Financial Modeling",
    "HR Management","Talent Acquisition","Recruitment","Performance Management",
    "Communication","Leadership","Team Management","Problem Solving","Critical Thinking",
    "Public Speaking","Presentation","Negotiation","Conflict Resolution",
    "Customer Support","Technical Writing","Documentation",
    "Operations","Supply Chain","Logistics","Quality Assurance",
]


@router.get("/suggest")
async def suggest_skills(q: str = "", current_user=Depends(get_current_user)):
    if not q:
        return SKILLS[:20]
    q_lower = q.lower()
    matches = [s for s in SKILLS if q_lower in s.lower()]
    return matches[:20]
