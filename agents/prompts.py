"""
AI Prompts for Web Development Agent
Contains all prompt templates used by different agents
"""

# Instruction Analysis Prompts
INSTRUCTION_ANALYSIS_PROMPT = """
You are an expert web developer and UX designer. Analyze the following user instruction for creating a website and extract structured information.

User Instruction: {instruction}

Please analyze this instruction and provide a JSON response with the following structure:

{{
    "website_type": "string (e.g., 'portfolio', 'business', 'blog', 'landing-page', 'e-commerce', 'documentation')",
    "pages": [
        {{
            "name": "string (page name like 'home', 'about', 'contact')",
            "purpose": "string (what this page is for)",
            "content_requirements": "string (specific content needed for this page)"
        }}
    ],
    "design_style": "string (e.g., 'modern', 'minimal', 'corporate', 'creative', 'dark', 'colorful')",
    "color_scheme": "string (preferred colors or color scheme)",
    "key_features": ["list of important features or functionality"],
    "target_audience": "string (who is the target audience)",
    "content_focus": "string (main focus of the website content)",
    "technical_requirements": ["list of specific technical needs"],
    "layout_preferences": "string (any specific layout preferences mentioned)"
}}

Important guidelines:
1. If the instruction is vague, make reasonable assumptions based on common website patterns
2. Always include at least a home page
3. Suggest additional pages that would be commonly needed for this type of website
4. Extract design preferences even if not explicitly stated
5. Focus on creating a cohesive website structure

Provide only the JSON response, no additional text.
"""

# Layout Generation Prompts
LAYOUT_GENERATION_PROMPT = """
You are an expert frontend developer specializing in modern web design with Next.js and TailwindCSS.

Create a website layout based on this analysis:
{analysis}

Generate a JSON response with the following structure:

{{
    "layout": {{
        "header": {{
            "type": "string (e.g., 'navbar', 'hero-header', 'simple')",
            "elements": ["list of header elements like 'logo', 'navigation', 'cta-button']",
            "style": "string (styling approach)"
        }},
        "footer": {{
            "type": "string (e.g., 'simple', 'detailed', 'minimal')",
            "elements": ["list of footer elements"],
            "style": "string (styling approach)"
        }},
        "navigation": {{
            "type": "string (e.g., 'horizontal', 'sidebar', 'mobile-friendly')",
            "items": [
                {{
                    "label": "string",
                    "href": "string (page route)"
                }}
            ]
        }},
        "color_palette": {{
            "primary": "string (hex color)",
            "secondary": "string (hex color)", 
            "accent": "string (hex color)",
            "background": "string (hex color)",
            "text": "string (hex color)"
        }},
        "typography": {{
            "headings": "string (font family for headings)",
            "body": "string (font family for body text)",
            "sizes": {{
                "h1": "string (tailwind class)",
                "h2": "string (tailwind class)",
                "h3": "string (tailwind class)",
                "body": "string (tailwind class)"
            }}
        }},
        "spacing": {{
            "section_padding": "string (tailwind class)",
            "container_max_width": "string (tailwind class)",
            "element_spacing": "string (tailwind class)"
        }}
    }},
    "components": [
        {{
            "name": "string (component name)",
            "type": "string (component type like 'hero', 'feature-grid', 'testimonial')",
            "description": "string (what this component does)",
            "props": ["list of props this component needs"]
        }}
    ]
}}

Design Guidelines:
1. Use modern, responsive design principles
2. Ensure accessibility (proper contrast, semantic HTML)
3. Use TailwindCSS classes for all styling
4. Create reusable components
5. Follow current web design trends
6. Ensure mobile-first responsive design
7. Use semantic color names and ensure good contrast
8. Include proper spacing and typography scale

Provide only the JSON response, no additional text.
"""

# Page Development Prompts
PAGE_DEVELOPMENT_PROMPT = """
You are an expert Next.js developer. Create a high-quality page component based on these specifications:

Page Information:
- Name: {page_name}
- Purpose: {page_purpose}
- Content Requirements: {content_requirements}

Layout Configuration:
{layout_config}

Create a Next.js page component with the following requirements:

1. Use TypeScript and functional components
2. Use TailwindCSS for all styling (follow the color palette and typography from layout)
3. Make it fully responsive (mobile-first approach)
4. Include proper SEO meta tags
5. Use semantic HTML elements
6. Ensure accessibility (ARIA labels, proper heading hierarchy)
7. Create engaging, realistic content (not just placeholder text)
8. Use modern React patterns (hooks, proper state management)
9. Include proper error handling where applicable
10. Follow Next.js 13+ app router conventions

Component Structure:
- Export as default function
- Include proper TypeScript types
- Use the layout's color palette and typography settings
- Create modular, reusable sub-components if needed
- Include proper loading states if applicable

Content Guidelines:
- Create realistic, engaging content (not lorem ipsum)
- Use professional, well-written copy
- Include relevant call-to-action elements
- Make content relevant to the page purpose
- Use proper heading hierarchy (h1, h2, h3)

Styling Guidelines:
- Follow the provided color palette exactly
- Use consistent spacing from layout configuration
- Ensure proper contrast ratios
- Use hover effects and transitions for interactive elements
- Make sure all elements are properly aligned and spaced
- Use the specified typography settings

Return your response in this JSON format:

{{
    "component_code": "string (complete Next.js component code)",
    "component_name": "string (component name)",
    "file_name": "string (file name like 'page.tsx')",
    "dependencies": ["array of any additional dependencies needed"],
    "description": "string (brief description of what this component does)"
}}

Important: 
- Provide COMPLETE, working code that can be directly used
- Do not use placeholder content - create realistic, engaging content
- Ensure all TailwindCSS classes are valid
- Follow React and Next.js best practices
- Make sure the code is production-ready

Provide only the JSON response, no additional text or code blocks.
"""

# Review Page Prompts
REVIEW_PAGE_PROMPT = """
You are an expert code reviewer specializing in Next.js, React, and web development best practices.

Review the following page component code and provide a detailed analysis:

Component Code:
{component_code}

Page Context:
- Page Name: {page_name}
- Purpose: {page_purpose}
- Layout Requirements: {layout_requirements}

Please analyze the code for:

1. **Code Quality** (25 points max):
   - TypeScript usage and type safety
   - React best practices and patterns
   - Code organization and structure
   - Error handling and edge cases
   - Performance considerations

2. **Design & Styling** (25 points max):
   - TailwindCSS usage and consistency
   - Responsive design implementation
   - Color palette adherence
   - Typography consistency
   - Visual hierarchy and spacing

3. **Functionality** (20 points max):
   - Component functionality and logic
   - Props and state management
   - Event handling
   - Integration with Next.js features
   - User interaction handling

4. **Accessibility** (15 points max):
   - Semantic HTML usage
   - ARIA labels and roles
   - Keyboard navigation support
   - Screen reader compatibility
   - Color contrast and readability

5. **Content Quality** (15 points max):
   - Realistic and engaging content
   - Proper content structure
   - SEO considerations
   - Call-to-action effectiveness
   - Content relevance to purpose

Provide your review in this JSON format:

{{
    "overall_score": "number (0-100)",
    "category_scores": {{
        "code_quality": "number (0-25)",
        "design_styling": "number (0-25)", 
        "functionality": "number (0-20)",
        "accessibility": "number (0-15)",
        "content_quality": "number (0-15)"
    }},
    "strengths": ["array of specific strengths found in the code"],
    "issues": [
        {{
            "severity": "string (critical/major/minor)",
            "category": "string (code_quality/design_styling/functionality/accessibility/content_quality)",
            "description": "string (detailed description of the issue)",
            "suggestion": "string (how to fix this issue)"
        }}
    ],
    "recommendations": ["array of general recommendations for improvement"],
    "passes_quality_check": "boolean (true if score >= 70, false otherwise)",
    "summary": "string (brief summary of the review)"
}}

Scoring Guidelines:
- 90-100: Excellent, production-ready code
- 80-89: Good code with minor improvements needed
- 70-79: Acceptable code with some issues to address
- 60-69: Below standard, needs significant improvements
- Below 60: Poor code quality, major rework needed

Be thorough, constructive, and specific in your feedback. Focus on actionable improvements.

Provide only the JSON response, no additional text.
"""

# Step Generation Prompts
STEP_GENERATION_PROMPT = """
You are a project manager for web development projects. Create a detailed step-by-step plan for building a website.

Project Analysis:
{analysis}

Layout Configuration:
{layout}

Create a comprehensive development plan with the following JSON structure:

{{
    "project_overview": {{
        "name": "string (project name)",
        "description": "string (brief project description)",
        "estimated_duration": "string (estimated time to complete)",
        "complexity_level": "string (simple/moderate/complex)"
    }},
    "steps": [
        {{
            "step_number": "number",
            "name": "string (step name)",
            "description": "string (detailed description)",
            "type": "string (setup/development/review/deployment)",
            "estimated_time": "string (estimated time for this step)",
            "dependencies": ["array of step numbers this depends on"],
            "deliverables": ["array of what will be produced in this step"],
            "success_criteria": ["array of criteria to consider this step complete"]
        }}
    ],
    "technical_stack": {{
        "frontend": ["array of frontend technologies"],
        "styling": ["array of styling frameworks/tools"],
        "deployment": ["array of deployment platforms"],
        "tools": ["array of development tools"]
    }},
    "quality_checkpoints": [
        {{
            "step": "number (which step this checkpoint applies to)",
            "checks": ["array of quality checks to perform"],
            "acceptance_criteria": ["array of criteria that must be met"]
        }}
    ],
    "risk_mitigation": [
        {{
            "risk": "string (potential risk)",
            "impact": "string (low/medium/high)",
            "mitigation": "string (how to mitigate this risk)"
        }}
    ]
}}

Step Types:
- "setup": Project initialization, environment setup
- "development": Actual coding and component creation
- "review": Code review, testing, quality assurance
- "deployment": Building and deploying the website

Guidelines:
1. Create logical, sequential steps
2. Include proper dependencies between steps
3. Provide realistic time estimates
4. Include quality checkpoints at appropriate intervals
5. Consider potential risks and how to mitigate them
6. Ensure each step has clear deliverables and success criteria
7. Include steps for responsive design testing
8. Add accessibility testing checkpoints
9. Include performance optimization steps

Provide only the JSON response, no additional text.
"""

# Build Agent Prompts
BUILD_PREPARATION_PROMPT = """
You are a build engineer specializing in Next.js applications. Analyze the project and prepare it for static export to AWS S3.

Project Information:
- Project ID: {project_id}
- Build Directory: {build_directory}
- Pages: {pages}

Create a build configuration and preparation plan in JSON format:

{{
    "build_config": {{
        "output_type": "export",
        "trailing_slash": true,
        "images_unoptimized": true,
        "static_optimization": true
    }},
    "next_config": {{
        "output": "export",
        "trailingSlash": true,
        "images": {{
            "unoptimized": true
        }},
        "assetPrefix": "",
        "basePath": ""
    }},
    "package_json_scripts": {{
        "build": "next build",
        "export": "next export",
        "build-static": "next build && next export"
    }},
    "build_steps": [
        {{
            "step": "string (step name)",
            "command": "string (command to run)",
            "description": "string (what this step does)",
            "expected_output": "string (expected result)"
        }}
    ],
    "validation_checks": [
        {{
            "check": "string (what to check)",
            "location": "string (where to check)",
            "success_criteria": "string (what indicates success)"
        }}
    ],
    "optimization_recommendations": [
        "string (optimization suggestions)"
    ]
}}

Ensure the configuration is optimized for:
1. Static site generation
2. AWS S3 hosting compatibility
3. Fast loading times
4. SEO optimization
5. Mobile performance

Provide only the JSON response, no additional text.
"""

# S3 Deployment Prompts
S3_DEPLOYMENT_PROMPT = """
You are a DevOps engineer specializing in AWS S3 static website deployments. Create a deployment plan for the website.

Deployment Information:
- Project ID: {project_id}
- Bucket Name: {bucket_name}
- Build Directory: {build_directory}
- Website Type: {website_type}

Create a comprehensive deployment plan in JSON format:

{{
    "deployment_config": {{
        "bucket_name": "string (S3 bucket name)",
        "region": "string (AWS region)",
        "website_hosting": true,
        "public_access": true,
        "cors_enabled": true
    }},
    "bucket_policy": {{
        "Version": "2012-10-17",
        "Statement": [
            {{
                "Sid": "PublicReadGetObject",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": "string (bucket ARN)"
            }}
        ]
    }},
    "website_configuration": {{
        "IndexDocument": {{
            "Suffix": "index.html"
        }},
        "ErrorDocument": {{
            "Key": "error.html"
        }}
    }},
    "deployment_steps": [
        {{
            "step": "string (step name)",
            "action": "string (AWS action)",
            "description": "string (what this step does)",
            "success_criteria": "string (how to verify success)"
        }}
    ],
    "post_deployment_checks": [
        {{
            "check": "string (what to verify)",
            "method": "string (how to check)",
            "expected_result": "string (what should happen)"
        }}
    ],
    "performance_optimizations": [
        "string (performance optimization suggestions)"
    ],
    "security_considerations": [
        "string (security best practices applied)"
    ]
}}

Ensure the deployment plan includes:
1. Proper S3 bucket configuration
2. Website hosting setup
3. Public access configuration
4. CORS setup if needed
5. Performance optimizations
6. Security best practices
7. Monitoring and validation steps

Provide only the JSON response, no additional text.
"""

# Execution Agent Prompts
EXECUTION_MONITORING_PROMPT = """
You are a development server monitor. Analyze the server startup process and provide status updates.

Server Information:
- Project ID: {project_id}
- Port: {port}
- Command: {command}
- Process Status: {status}

Monitor the development server and provide status in JSON format:

{{
    "server_status": {{
        "running": "boolean",
        "port": "number",
        "url": "string (local server URL)",
        "process_id": "number or null",
        "startup_time": "string (time taken to start)"
    }},
    "compilation_status": {{
        "successful": "boolean",
        "errors": ["array of compilation errors if any"],
        "warnings": ["array of compilation warnings if any"],
        "pages_compiled": "number"
    }},
    "health_checks": [
        {{
            "check": "string (what was checked)",
            "status": "string (pass/fail/warning)",
            "details": "string (additional details)"
        }}
    ],
    "performance_metrics": {{
        "initial_compile_time": "string",
        "memory_usage": "string",
        "bundle_size": "string"
    }},
    "recommendations": [
        "string (performance or optimization recommendations)"
    ],
    "next_actions": [
        "string (suggested next steps)"
    ]
}}

Focus on:
1. Server startup success/failure
2. Compilation status and errors
3. Performance metrics
4. Accessibility of the development server
5. Any issues that need attention

Provide only the JSON response, no additional text.
"""

# Error Handling Prompts
ERROR_ANALYSIS_PROMPT = """
You are a debugging expert specializing in Next.js and React applications. Analyze the error and provide solutions.

Error Information:
- Error Type: {error_type}
- Error Message: {error_message}
- Stack Trace: {stack_trace}
- Context: {context}

Analyze the error and provide a solution plan in JSON format:

{{
    "error_analysis": {{
        "category": "string (compilation/runtime/build/deployment)",
        "severity": "string (critical/major/minor)",
        "root_cause": "string (likely cause of the error)",
        "affected_components": ["array of affected files/components"]
    }},
    "solutions": [
        {{
            "approach": "string (solution approach)",
            "steps": ["array of steps to implement this solution"],
            "confidence": "string (high/medium/low)",
            "estimated_time": "string (time to implement)",
            "risk_level": "string (low/medium/high)"
        }}
    ],
    "quick_fixes": [
        {{
            "fix": "string (quick fix description)",
            "command": "string (command to run if applicable)",
            "file_changes": [
                {{
                    "file": "string (file path)",
                    "change": "string (what to change)"
                }}
            ]
        }}
    ],
    "prevention_measures": [
        "string (how to prevent this error in the future)"
    ],
    "related_issues": [
        "string (other potential issues to watch for)"
    ]
}}

Provide practical, actionable solutions that can be implemented immediately.

Provide only the JSON response, no additional text.
"""

# Quality Control Prompts
QUALITY_ASSESSMENT_PROMPT = """
You are a quality assurance engineer for web applications. Assess the overall quality of the website project.

Project Information:
- Project ID: {project_id}
- Pages Created: {pages_created}
- Components: {components}
- Build Status: {build_status}
- Deployment Status: {deployment_status}

Provide a comprehensive quality assessment in JSON format:

{{
    "overall_quality_score": "number (0-100)",
    "quality_categories": {{
        "code_quality": {{
            "score": "number (0-25)",
            "details": "string (assessment details)"
        }},
        "design_consistency": {{
            "score": "number (0-20)",
            "details": "string (assessment details)"
        }},
        "functionality": {{
            "score": "number (0-20)",
            "details": "string (assessment details)"
        }},
        "performance": {{
            "score": "number (0-15)",
            "details": "string (assessment details)"
        }},
        "accessibility": {{
            "score": "number (0-10)",
            "details": "string (assessment details)"
        }},
        "seo_readiness": {{
            "score": "number (0-10)",
            "details": "string (assessment details)"
        }}
    }},
    "strengths": ["array of project strengths"],
    "areas_for_improvement": [
        {{
            "area": "string (area needing improvement)",
            "priority": "string (high/medium/low)",
            "recommendation": "string (specific recommendation)"
        }}
    ],
    "compliance_checks": [
        {{
            "standard": "string (web standard or best practice)",
            "status": "string (compliant/partial/non-compliant)",
            "notes": "string (additional notes)"
        }}
    ],
    "deployment_readiness": {{
        "ready": "boolean",
        "blockers": ["array of issues preventing deployment"],
        "recommendations": ["array of pre-deployment recommendations"]
    }},
    "maintenance_considerations": [
        "string (ongoing maintenance recommendations)"
    ]
}}

Assessment Criteria:
- Code follows best practices and is maintainable
- Design is consistent and professional
- All functionality works as expected
- Performance is optimized for web delivery
- Accessibility standards are met
- SEO basics are implemented
- Project is ready for production deployment

Provide only the JSON response, no additional text.
"""

# Workflow Orchestration Prompts
WORKFLOW_STATUS_PROMPT = """
You are a project orchestrator monitoring the website creation workflow. Provide status updates and next actions.

Workflow State:
- Current Step: {current_step}
- Completed Steps: {completed_steps}
- Pending Steps: {pending_steps}
- Project Status: {project_status}
- Any Errors: {errors}

Provide workflow status and recommendations in JSON format:

{{
    "workflow_status": {{
        "current_phase": "string (analysis/design/development/review/build/deploy)",
        "progress_percentage": "number (0-100)",
        "estimated_completion": "string (time estimate)",
        "status": "string (on_track/delayed/blocked/completed)"
    }},
    "step_status": [
        {{
            "step_name": "string",
            "status": "string (pending/in_progress/completed/failed)",
            "duration": "string (time taken or estimated)",
            "output": "string (key deliverable or result)"
        }}
    ],
    "current_actions": [
        "string (what is currently happening)"
    ],
    "next_actions": [
        {{
            "action": "string (next action to take)",
            "priority": "string (high/medium/low)",
            "estimated_time": "string (time estimate)",
            "dependencies": ["array of dependencies"]
        }}
    ],
    "quality_gates": [
        {{
            "gate": "string (quality checkpoint)",
            "status": "string (passed/pending/failed)",
            "criteria": ["array of criteria for this gate"]
        }}
    ],
    "risks_and_issues": [
        {{
            "type": "string (risk/issue)",
            "description": "string (description)",
            "impact": "string (low/medium/high)",
            "mitigation": "string (how to address)"
        }}
    ],
    "recommendations": [
        "string (workflow improvement recommendations)"
    ]
}}

Focus on:
1. Clear status of where we are in the workflow
2. What's working well and what needs attention
3. Realistic time estimates for remaining work
4. Quality checkpoints and their status
5. Any blockers or risks that need addressing

Provide only the JSON response, no additional text.
"""