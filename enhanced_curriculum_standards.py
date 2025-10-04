#!/usr/bin/env python3
"""
Enhanced Curriculum Standards Definition
Precise mapping of Ontario and US high school curriculum standards
Based on official education ministry documents
"""

from typing import Dict, List, Any
import json

class EnhancedCurriculumStandards:
    """
    Enhanced curriculum standards based on official Ontario and US education documents
    """
    
    def __init__(self):
        self.standards = self._define_enhanced_standards()
    
    def _define_enhanced_standards(self) -> Dict[str, Any]:
        """
        Define enhanced curriculum standards based on official documents
        """
        return {
            "Ontario_Standards": {
                "Mathematics": {
                    "Grade_9": {
                        "Mathematics_9": {
                            "description": "Foundational mathematics concepts and skills",
                            "topics": [
                                {
                                    "name": "Number Sense and Operations",
                                    "subtopics": [
                                        "Rational numbers and operations",
                                        "Exponents and scientific notation",
                                        "Square roots and cube roots",
                                        "Financial literacy and compound interest"
                                    ],
                                    "difficulty_levels": ["beginner", "intermediate"]
                                },
                                {
                                    "name": "Algebra and Patterns",
                                    "subtopics": [
                                        "Linear relationships and equations",
                                        "Graphing linear functions",
                                        "Systems of linear equations",
                                        "Polynomial expressions and operations"
                                    ],
                                    "difficulty_levels": ["beginner", "intermediate"]
                                },
                                {
                                    "name": "Geometry and Measurement",
                                    "subtopics": [
                                        "Properties of geometric shapes",
                                        "Pythagorean theorem",
                                        "Surface area and volume",
                                        "Coordinate geometry basics"
                                    ],
                                    "difficulty_levels": ["beginner", "intermediate"]
                                },
                                {
                                    "name": "Data Management and Probability",
                                    "subtopics": [
                                        "Data collection and analysis",
                                        "Statistical measures",
                                        "Probability concepts",
                                        "Graphical representations"
                                    ],
                                    "difficulty_levels": ["beginner", "intermediate"]
                                }
                            ]
                        }
                    },
                    "Grade_10": {
                        "Mathematics_10": {
                            "description": "Intermediate mathematics building on Grade 9 foundations",
                            "topics": [
                                {
                                    "name": "Linear Relations",
                                    "subtopics": [
                                        "Slope and rate of change",
                                        "Linear functions and graphs",
                                        "Linear systems",
                                        "Linear inequalities"
                                    ],
                                    "difficulty_levels": ["intermediate"]
                                },
                                {
                                    "name": "Quadratic Relations",
                                    "subtopics": [
                                        "Quadratic functions and graphs",
                                        "Factoring quadratic expressions",
                                        "Quadratic formula",
                                        "Applications of quadratics"
                                    ],
                                    "difficulty_levels": ["intermediate", "advanced"]
                                },
                                {
                                    "name": "Trigonometry",
                                    "subtopics": [
                                        "Right triangle trigonometry",
                                        "Sine, cosine, and tangent ratios",
                                        "Solving right triangles",
                                        "Applications of trigonometry"
                                    ],
                                    "difficulty_levels": ["intermediate", "advanced"]
                                },
                                {
                                    "name": "Analytic Geometry",
                                    "subtopics": [
                                        "Distance and midpoint formulas",
                                        "Equation of a circle",
                                        "Properties of lines",
                                        "Coordinate proofs"
                                    ],
                                    "difficulty_levels": ["intermediate", "advanced"]
                                }
                            ]
                        }
                    },
                    "Grade_11": {
                        "Functions_11": {
                            "description": "Advanced function concepts and applications",
                            "topics": [
                                {
                                    "name": "Quadratic Functions",
                                    "subtopics": [
                                        "Vertex form and standard form",
                                        "Transformations of quadratic functions",
                                        "Maximum and minimum values",
                                        "Quadratic inequalities"
                                    ],
                                    "difficulty_levels": ["advanced"]
                                },
                                {
                                    "name": "Exponential Functions",
                                    "subtopics": [
                                        "Exponential growth and decay",
                                        "Compound interest applications",
                                        "Exponential equations",
                                        "Logarithmic functions"
                                    ],
                                    "difficulty_levels": ["advanced"]
                                },
                                {
                                    "name": "Trigonometric Functions",
                                    "subtopics": [
                                        "Unit circle and radian measure",
                                        "Graphs of sine, cosine, and tangent",
                                        "Trigonometric identities",
                                        "Solving trigonometric equations"
                                    ],
                                    "difficulty_levels": ["advanced", "expert"]
                                },
                                {
                                    "name": "Discrete Functions",
                                    "subtopics": [
                                        "Sequences and series",
                                        "Arithmetic and geometric progressions",
                                        "Financial applications",
                                        "Recursive functions"
                                    ],
                                    "difficulty_levels": ["advanced"]
                                }
                            ]
                        }
                    },
                    "Grade_12": {
                        "Advanced_Functions": {
                            "description": "Pre-calculus preparation with advanced function concepts",
                            "topics": [
                                {
                                    "name": "Polynomial Functions",
                                    "subtopics": [
                                        "Polynomial division and factoring",
                                        "Rational root theorem",
                                        "Graphs of polynomial functions",
                                        "Polynomial inequalities"
                                    ],
                                    "difficulty_levels": ["expert"]
                                },
                                {
                                    "name": "Exponential and Logarithmic Functions",
                                    "subtopics": [
                                        "Properties of logarithms",
                                        "Exponential and logarithmic equations",
                                        "Applications in science and finance",
                                        "Natural logarithms and e"
                                    ],
                                    "difficulty_levels": ["expert"]
                                },
                                {
                                    "name": "Trigonometric Functions",
                                    "subtopics": [
                                        "Advanced trigonometric identities",
                                        "Sum and difference formulas",
                                        "Double and half angle formulas",
                                        "Trigonometric equations and inequalities"
                                    ],
                                    "difficulty_levels": ["expert"]
                                },
                                {
                                    "name": "Combinations of Functions",
                                    "subtopics": [
                                        "Function composition",
                                        "Inverse functions",
                                        "Transformations of functions",
                                        "Piecewise functions"
                                    ],
                                    "difficulty_levels": ["expert"]
                                }
                            ]
                        },
                        "Calculus_and_Vectors": {
                            "description": "Introduction to calculus and vector mathematics",
                            "topics": [
                                {
                                    "name": "Limits and Continuity",
                                    "subtopics": [
                                        "Concept of limits",
                                        "Limit laws and properties",
                                        "Continuity and discontinuity",
                                        "Asymptotes and end behavior"
                                    ],
                                    "difficulty_levels": ["expert"]
                                },
                                {
                                    "name": "Derivatives",
                                    "subtopics": [
                                        "Definition of derivative",
                                        "Power rule and basic differentiation",
                                        "Product and quotient rules",
                                        "Chain rule and implicit differentiation"
                                    ],
                                    "difficulty_levels": ["expert"]
                                },
                                {
                                    "name": "Applications of Derivatives",
                                    "subtopics": [
                                        "Related rates problems",
                                        "Optimization problems",
                                        "Curve sketching",
                                        "Newton's method"
                                    ],
                                    "difficulty_levels": ["expert"]
                                },
                                {
                                    "name": "Integrals",
                                    "subtopics": [
                                        "Antiderivatives and indefinite integrals",
                                        "Fundamental theorem of calculus",
                                        "Definite integrals and area",
                                        "Integration techniques"
                                    ],
                                    "difficulty_levels": ["expert"]
                                },
                                {
                                    "name": "Vectors in Two and Three Dimensions",
                                    "subtopics": [
                                        "Vector operations and properties",
                                        "Dot product and cross product",
                                        "Lines and planes in 3D",
                                        "Applications of vectors"
                                    ],
                                    "difficulty_levels": ["expert"]
                                }
                            ]
                        },
                        "Data_Management": {
                            "description": "Advanced statistics and probability",
                            "topics": [
                                {
                                    "name": "Probability",
                                    "subtopics": [
                                        "Conditional probability",
                                        "Bayes' theorem",
                                        "Permutations and combinations",
                                        "Probability distributions"
                                    ],
                                    "difficulty_levels": ["advanced", "expert"]
                                },
                                {
                                    "name": "Statistics",
                                    "subtopics": [
                                        "Descriptive statistics",
                                        "Inferential statistics",
                                        "Hypothesis testing",
                                        "Confidence intervals"
                                    ],
                                    "difficulty_levels": ["advanced", "expert"]
                                },
                                {
                                    "name": "Distributions",
                                    "subtopics": [
                                        "Normal distribution",
                                        "Binomial distribution",
                                        "Sampling distributions",
                                        "Central limit theorem"
                                    ],
                                    "difficulty_levels": ["expert"]
                                },
                                {
                                    "name": "Regression Analysis",
                                    "subtopics": [
                                        "Linear regression",
                                        "Correlation analysis",
                                        "Residual analysis",
                                        "Non-linear regression"
                                    ],
                                    "difficulty_levels": ["expert"]
                                }
                            ]
                        }
                    }
                },
                "Physics": {
                    "Grade_11": {
                        "Physics_11": {
                            "description": "Introduction to physics concepts and principles",
                            "topics": [
                                {
                                    "name": "Kinematics",
                                    "subtopics": [
                                        "Motion in one dimension",
                                        "Motion in two dimensions",
                                        "Projectile motion",
                                        "Relative motion"
                                    ],
                                    "difficulty_levels": ["intermediate", "advanced"]
                                },
                                {
                                    "name": "Forces and Motion",
                                    "subtopics": [
                                        "Newton's laws of motion",
                                        "Friction and normal forces",
                                        "Circular motion",
                                        "Gravitational forces"
                                    ],
                                    "difficulty_levels": ["intermediate", "advanced"]
                                },
                                {
                                    "name": "Energy and Momentum",
                                    "subtopics": [
                                        "Work and energy",
                                        "Conservation of energy",
                                        "Momentum and impulse",
                                        "Collisions"
                                    ],
                                    "difficulty_levels": ["advanced"]
                                },
                                {
                                    "name": "Waves and Sound",
                                    "subtopics": [
                                        "Wave properties",
                                        "Sound waves and frequency",
                                        "Interference and resonance",
                                        "Doppler effect"
                                    ],
                                    "difficulty_levels": ["intermediate", "advanced"]
                                },
                                {
                                    "name": "Light and Geometric Optics",
                                    "subtopics": [
                                        "Reflection and refraction",
                                        "Mirrors and lenses",
                                        "Total internal reflection",
                                        "Optical instruments"
                                    ],
                                    "difficulty_levels": ["advanced"]
                                }
                            ]
                        }
                    },
                    "Grade_12": {
                        "Physics_12": {
                            "description": "Advanced physics concepts and modern physics",
                            "topics": [
                                {
                                    "name": "Forces and Motion",
                                    "subtopics": [
                                        "Advanced dynamics",
                                        "Rotational motion",
                                        "Simple harmonic motion",
                                        "Gravitational fields"
                                    ],
                                    "difficulty_levels": ["expert"]
                                },
                                {
                                    "name": "Energy and Momentum",
                                    "subtopics": [
                                        "Advanced energy concepts",
                                        "Conservation laws",
                                        "Elastic and inelastic collisions",
                                        "Energy transformations"
                                    ],
                                    "difficulty_levels": ["expert"]
                                },
                                {
                                    "name": "Electric and Magnetic Fields",
                                    "subtopics": [
                                        "Electric fields and forces",
                                        "Magnetic fields and forces",
                                        "Electromagnetic induction",
                                        "AC circuits"
                                    ],
                                    "difficulty_levels": ["expert"]
                                },
                                {
                                    "name": "Electromagnetic Radiation",
                                    "subtopics": [
                                        "Electromagnetic spectrum",
                                        "Wave-particle duality",
                                        "Photoelectric effect",
                                        "Electromagnetic waves"
                                    ],
                                    "difficulty_levels": ["expert"]
                                },
                                {
                                    "name": "Quantum Mechanics",
                                    "subtopics": [
                                        "Quantum theory basics",
                                        "Atomic structure",
                                        "Quantum numbers",
                                        "Uncertainty principle"
                                    ],
                                    "difficulty_levels": ["expert"]
                                },
                                {
                                    "name": "Special Relativity",
                                    "subtopics": [
                                        "Time dilation",
                                        "Length contraction",
                                        "Mass-energy equivalence",
                                        "Relativistic momentum"
                                    ],
                                    "difficulty_levels": ["expert"]
                                }
                            ]
                        }
                    }
                }
            },
            "US_Standards": {
                "Mathematics": {
                    "Grade_9": {
                        "Algebra_I": {
                            "description": "Foundational algebra concepts and problem-solving",
                            "topics": [
                                {
                                    "name": "Linear Equations and Inequalities",
                                    "subtopics": [
                                        "Solving linear equations",
                                        "Graphing linear equations",
                                        "Systems of linear equations",
                                        "Linear inequalities"
                                    ],
                                    "difficulty_levels": ["beginner", "intermediate"]
                                },
                                {
                                    "name": "Functions and Relations",
                                    "subtopics": [
                                        "Function notation",
                                        "Domain and range",
                                        "Linear functions",
                                        "Function transformations"
                                    ],
                                    "difficulty_levels": ["beginner", "intermediate"]
                                },
                                {
                                    "name": "Polynomials and Factoring",
                                    "subtopics": [
                                        "Polynomial operations",
                                        "Factoring techniques",
                                        "Quadratic expressions",
                                        "Polynomial division"
                                    ],
                                    "difficulty_levels": ["intermediate"]
                                },
                                {
                                    "name": "Quadratic Functions",
                                    "subtopics": [
                                        "Graphing quadratics",
                                        "Vertex form",
                                        "Quadratic formula",
                                        "Applications of quadratics"
                                    ],
                                    "difficulty_levels": ["intermediate", "advanced"]
                                },
                                {
                                    "name": "Exponential Functions",
                                    "subtopics": [
                                        "Exponential growth and decay",
                                        "Compound interest",
                                        "Exponential equations",
                                        "Graphing exponentials"
                                    ],
                                    "difficulty_levels": ["intermediate", "advanced"]
                                },
                                {
                                    "name": "Data Analysis and Statistics",
                                    "subtopics": [
                                        "Statistical measures",
                                        "Data representation",
                                        "Correlation and regression",
                                        "Probability basics"
                                    ],
                                    "difficulty_levels": ["beginner", "intermediate"]
                                }
                            ]
                        }
                    },
                    "Grade_10": {
                        "Geometry": {
                            "description": "Geometric reasoning and spatial relationships",
                            "topics": [
                                {
                                    "name": "Points, Lines, and Planes",
                                    "subtopics": [
                                        "Basic geometric concepts",
                                        "Postulates and theorems",
                                        "Angle relationships",
                                        "Parallel and perpendicular lines"
                                    ],
                                    "difficulty_levels": ["beginner", "intermediate"]
                                },
                                {
                                    "name": "Triangles and Congruence",
                                    "subtopics": [
                                        "Triangle properties",
                                        "Congruence theorems",
                                        "Similar triangles",
                                        "Triangle inequalities"
                                    ],
                                    "difficulty_levels": ["intermediate"]
                                },
                                {
                                    "name": "Quadrilaterals",
                                    "subtopics": [
                                        "Properties of quadrilaterals",
                                        "Parallelograms and special cases",
                                        "Coordinate geometry",
                                        "Proofs with quadrilaterals"
                                    ],
                                    "difficulty_levels": ["intermediate", "advanced"]
                                },
                                {
                                    "name": "Right Triangles and Trigonometry",
                                    "subtopics": [
                                        "Pythagorean theorem",
                                        "Special right triangles",
                                        "Trigonometric ratios",
                                        "Applications of trigonometry"
                                    ],
                                    "difficulty_levels": ["intermediate", "advanced"]
                                },
                                {
                                    "name": "Circles and Arcs",
                                    "subtopics": [
                                        "Circle properties",
                                        "Arc and chord relationships",
                                        "Inscribed angles",
                                        "Circle equations"
                                    ],
                                    "difficulty_levels": ["intermediate", "advanced"]
                                },
                                {
                                    "name": "Area and Perimeter",
                                    "subtopics": [
                                        "Area formulas",
                                        "Perimeter calculations",
                                        "Composite figures",
                                        "Surface area and volume"
                                    ],
                                    "difficulty_levels": ["beginner", "intermediate"]
                                }
                            ]
                        }
                    },
                    "Grade_11": {
                        "Algebra_II": {
                            "description": "Advanced algebraic concepts and functions",
                            "topics": [
                                {
                                    "name": "Complex Numbers",
                                    "subtopics": [
                                        "Imaginary and complex numbers",
                                        "Operations with complex numbers",
                                        "Complex plane",
                                        "Quadratic formula with complex solutions"
                                    ],
                                    "difficulty_levels": ["advanced"]
                                },
                                {
                                    "name": "Polynomial Functions",
                                    "subtopics": [
                                        "Polynomial operations",
                                        "Graphing polynomial functions",
                                        "Polynomial division",
                                        "Rational root theorem"
                                    ],
                                    "difficulty_levels": ["advanced"]
                                },
                                {
                                    "name": "Rational Functions",
                                    "subtopics": [
                                        "Rational expressions",
                                        "Graphing rational functions",
                                        "Asymptotes and holes",
                                        "Rational equations"
                                    ],
                                    "difficulty_levels": ["advanced", "expert"]
                                },
                                {
                                    "name": "Exponential and Logarithmic Functions",
                                    "subtopics": [
                                        "Properties of logarithms",
                                        "Exponential and logarithmic equations",
                                        "Change of base formula",
                                        "Applications in science"
                                    ],
                                    "difficulty_levels": ["advanced", "expert"]
                                },
                                {
                                    "name": "Trigonometric Functions",
                                    "subtopics": [
                                        "Unit circle",
                                        "Trigonometric functions",
                                        "Graphs of trig functions",
                                        "Trigonometric identities"
                                    ],
                                    "difficulty_levels": ["advanced", "expert"]
                                },
                                {
                                    "name": "Sequences and Series",
                                    "subtopics": [
                                        "Arithmetic sequences",
                                        "Geometric sequences",
                                        "Series and summation",
                                        "Mathematical induction"
                                    ],
                                    "difficulty_levels": ["advanced"]
                                },
                                {
                                    "name": "Probability and Statistics",
                                    "subtopics": [
                                        "Advanced probability",
                                        "Statistical distributions",
                                        "Hypothesis testing",
                                        "Regression analysis"
                                    ],
                                    "difficulty_levels": ["advanced", "expert"]
                                },
                                {
                                    "name": "Conic Sections",
                                    "subtopics": [
                                        "Circles and ellipses",
                                        "Parabolas and hyperbolas",
                                        "Conic equations",
                                        "Applications of conics"
                                    ],
                                    "difficulty_levels": ["expert"]
                                }
                            ]
                        }
                    },
                    "Grade_12": {
                        "Pre_Calculus": {
                            "description": "Preparation for calculus with advanced function concepts",
                            "topics": [
                                {
                                    "name": "Advanced Functions",
                                    "subtopics": [
                                        "Function composition",
                                        "Inverse functions",
                                        "Function transformations",
                                        "Piecewise functions"
                                    ],
                                    "difficulty_levels": ["expert"]
                                },
                                {
                                    "name": "Trigonometric Identities",
                                    "subtopics": [
                                        "Fundamental identities",
                                        "Sum and difference formulas",
                                        "Double and half angle formulas",
                                        "Trigonometric equations"
                                    ],
                                    "difficulty_levels": ["expert"]
                                },
                                {
                                    "name": "Polar Coordinates",
                                    "subtopics": [
                                        "Polar coordinate system",
                                        "Converting between coordinate systems",
                                        "Polar equations and graphs",
                                        "Applications of polar coordinates"
                                    ],
                                    "difficulty_levels": ["expert"]
                                },
                                {
                                    "name": "Vectors",
                                    "subtopics": [
                                        "Vector operations",
                                        "Dot product and cross product",
                                        "Vector applications",
                                        "Parametric equations"
                                    ],
                                    "difficulty_levels": ["expert"]
                                },
                                {
                                    "name": "Matrices",
                                    "subtopics": [
                                        "Matrix operations",
                                        "Matrix multiplication",
                                        "Determinants and inverses",
                                        "Systems of equations with matrices"
                                    ],
                                    "difficulty_levels": ["expert"]
                                },
                                {
                                    "name": "Limits and Continuity",
                                    "subtopics": [
                                        "Introduction to limits",
                                        "Limit laws",
                                        "Continuity",
                                        "Asymptotes"
                                    ],
                                    "difficulty_levels": ["expert"]
                                }
                            ]
                        },
                        "Calculus": {
                            "description": "Introduction to differential and integral calculus",
                            "topics": [
                                {
                                    "name": "Derivatives",
                                    "subtopics": [
                                        "Definition of derivative",
                                        "Power rule and basic rules",
                                        "Product and quotient rules",
                                        "Chain rule"
                                    ],
                                    "difficulty_levels": ["expert"]
                                },
                                {
                                    "name": "Applications of Derivatives",
                                    "subtopics": [
                                        "Related rates",
                                        "Optimization problems",
                                        "Curve sketching",
                                        "Mean value theorem"
                                    ],
                                    "difficulty_levels": ["expert"]
                                },
                                {
                                    "name": "Integrals",
                                    "subtopics": [
                                        "Antiderivatives",
                                        "Fundamental theorem of calculus",
                                        "Definite integrals",
                                        "Integration techniques"
                                    ],
                                    "difficulty_levels": ["expert"]
                                },
                                {
                                    "name": "Applications of Integrals",
                                    "subtopics": [
                                        "Area under curves",
                                        "Volume of revolution",
                                        "Arc length",
                                        "Work and fluid pressure"
                                    ],
                                    "difficulty_levels": ["expert"]
                                },
                                {
                                    "name": "Differential Equations",
                                    "subtopics": [
                                        "Separable differential equations",
                                        "First-order linear equations",
                                        "Applications of differential equations",
                                        "Slope fields"
                                    ],
                                    "difficulty_levels": ["expert"]
                                }
                            ]
                        }
                    }
                },
                "Physics": {
                    "Grade_9": {
                        "Physical_Science": {
                            "description": "Introduction to physical science concepts",
                            "topics": [
                                {
                                    "name": "Motion and Forces",
                                    "subtopics": [
                                        "Basic motion concepts",
                                        "Newton's laws",
                                        "Friction and forces",
                                        "Simple machines"
                                    ],
                                    "difficulty_levels": ["beginner", "intermediate"]
                                },
                                {
                                    "name": "Energy and Work",
                                    "subtopics": [
                                        "Forms of energy",
                                        "Energy conservation",
                                        "Work and power",
                                        "Energy transformations"
                                    ],
                                    "difficulty_levels": ["beginner", "intermediate"]
                                },
                                {
                                    "name": "Waves and Sound",
                                    "subtopics": [
                                        "Wave properties",
                                        "Sound waves",
                                        "Frequency and wavelength",
                                        "Wave interference"
                                    ],
                                    "difficulty_levels": ["beginner", "intermediate"]
                                },
                                {
                                    "name": "Light and Optics",
                                    "subtopics": [
                                        "Light properties",
                                        "Reflection and refraction",
                                        "Mirrors and lenses",
                                        "Color and light"
                                    ],
                                    "difficulty_levels": ["beginner", "intermediate"]
                                },
                                {
                                    "name": "Electricity Basics",
                                    "subtopics": [
                                        "Electric charge",
                                        "Electric current",
                                        "Simple circuits",
                                        "Electrical safety"
                                    ],
                                    "difficulty_levels": ["beginner", "intermediate"]
                                },
                                {
                                    "name": "Magnetism Basics",
                                    "subtopics": [
                                        "Magnetic properties",
                                        "Magnetic fields",
                                        "Electromagnetism",
                                        "Applications of magnetism"
                                    ],
                                    "difficulty_levels": ["beginner", "intermediate"]
                                }
                            ]
                        }
                    },
                    "Grade_10": {
                        "Physics_I": {
                            "description": "Algebra-based physics with mathematical applications",
                            "topics": [
                                {
                                    "name": "Kinematics",
                                    "subtopics": [
                                        "Motion in one dimension",
                                        "Motion in two dimensions",
                                        "Projectile motion",
                                        "Graphical analysis of motion"
                                    ],
                                    "difficulty_levels": ["intermediate", "advanced"]
                                },
                                {
                                    "name": "Dynamics",
                                    "subtopics": [
                                        "Newton's laws of motion",
                                        "Force analysis",
                                        "Friction and normal forces",
                                        "Circular motion"
                                    ],
                                    "difficulty_levels": ["intermediate", "advanced"]
                                },
                                {
                                    "name": "Energy and Momentum",
                                    "subtopics": [
                                        "Work and energy theorem",
                                        "Conservation of energy",
                                        "Momentum and impulse",
                                        "Elastic and inelastic collisions"
                                    ],
                                    "difficulty_levels": ["advanced"]
                                },
                                {
                                    "name": "Rotational Motion",
                                    "subtopics": [
                                        "Angular kinematics",
                                        "Torque and angular acceleration",
                                        "Rotational dynamics",
                                        "Conservation of angular momentum"
                                    ],
                                    "difficulty_levels": ["advanced", "expert"]
                                },
                                {
                                    "name": "Simple Harmonic Motion",
                                    "subtopics": [
                                        "Oscillatory motion",
                                        "Pendulums and springs",
                                        "Wave motion",
                                        "Resonance"
                                    ],
                                    "difficulty_levels": ["advanced"]
                                },
                                {
                                    "name": "Fluid Mechanics",
                                    "subtopics": [
                                        "Pressure and buoyancy",
                                        "Fluid flow",
                                        "Bernoulli's principle",
                                        "Applications of fluid mechanics"
                                    ],
                                    "difficulty_levels": ["advanced", "expert"]
                                }
                            ]
                        }
                    },
                    "Grade_11": {
                        "Physics_II": {
                            "description": "Advanced physics concepts with calculus applications",
                            "topics": [
                                {
                                    "name": "Electric Fields and Forces",
                                    "subtopics": [
                                        "Electric charge and field",
                                        "Coulomb's law",
                                        "Electric potential",
                                        "Capacitors and dielectrics"
                                    ],
                                    "difficulty_levels": ["expert"]
                                },
                                {
                                    "name": "Magnetic Fields and Forces",
                                    "subtopics": [
                                        "Magnetic fields",
                                        "Magnetic force on moving charges",
                                        "Magnetic force on current-carrying wires",
                                        "Applications of magnetic forces"
                                    ],
                                    "difficulty_levels": ["expert"]
                                },
                                {
                                    "name": "Electromagnetic Induction",
                                    "subtopics": [
                                        "Faraday's law",
                                        "Lenz's law",
                                        "Induced EMF",
                                        "AC generators and motors"
                                    ],
                                    "difficulty_levels": ["expert"]
                                },
                                {
                                    "name": "AC Circuits",
                                    "subtopics": [
                                        "Alternating current",
                                        "Impedance and reactance",
                                        "Resonance in AC circuits",
                                        "Power in AC circuits"
                                    ],
                                    "difficulty_levels": ["expert"]
                                },
                                {
                                    "name": "Wave Properties",
                                    "subtopics": [
                                        "Wave equation",
                                        "Interference and diffraction",
                                        "Standing waves",
                                        "Wave-particle duality"
                                    ],
                                    "difficulty_levels": ["expert"]
                                },
                                {
                                    "name": "Optics and Interference",
                                    "subtopics": [
                                        "Light interference",
                                        "Diffraction patterns",
                                        "Polarization",
                                        "Optical instruments"
                                    ],
                                    "difficulty_levels": ["expert"]
                                }
                            ]
                        }
                    },
                    "Grade_12": {
                        "AP_Physics": {
                            "description": "Advanced placement physics with college-level content",
                            "topics": [
                                {
                                    "name": "Advanced Mechanics",
                                    "subtopics": [
                                        "Advanced dynamics",
                                        "Rotational motion and dynamics",
                                        "Gravitational fields",
                                        "Oscillatory motion"
                                    ],
                                    "difficulty_levels": ["expert"]
                                },
                                {
                                    "name": "Thermodynamics",
                                    "subtopics": [
                                        "Heat and temperature",
                                        "Laws of thermodynamics",
                                        "Heat engines and refrigerators",
                                        "Entropy and disorder"
                                    ],
                                    "difficulty_levels": ["expert"]
                                },
                                {
                                    "name": "Electromagnetic Fields",
                                    "subtopics": [
                                        "Maxwell's equations",
                                        "Electromagnetic waves",
                                        "Electromagnetic radiation",
                                        "Applications of EM fields"
                                    ],
                                    "difficulty_levels": ["expert"]
                                },
                                {
                                    "name": "Quantum Mechanics",
                                    "subtopics": [
                                        "Wave-particle duality",
                                        "Uncertainty principle",
                                        "Quantum states",
                                        "Applications of quantum mechanics"
                                    ],
                                    "difficulty_levels": ["expert"]
                                },
                                {
                                    "name": "Special Relativity",
                                    "subtopics": [
                                        "Einstein's postulates",
                                        "Time dilation and length contraction",
                                        "Mass-energy equivalence",
                                        "Relativistic momentum and energy"
                                    ],
                                    "difficulty_levels": ["expert"]
                                },
                                {
                                    "name": "Nuclear Physics",
                                    "subtopics": [
                                        "Nuclear structure",
                                        "Radioactive decay",
                                        "Nuclear reactions",
                                        "Applications of nuclear physics"
                                    ],
                                    "difficulty_levels": ["expert"]
                                }
                            ]
                        }
                    }
                }
            }
        }
    
    def get_curriculum_structure(self, country: str, subject: str) -> Dict[str, Any]:
        """
        Get curriculum structure for a specific country and subject
        
        Args:
            country: 'Ontario' or 'US'
            subject: 'Mathematics' or 'Physics'
            
        Returns:
            Curriculum structure for the specified country and subject
        """
        if country == 'Ontario':
            return self.standards['Ontario_Standards'].get(subject, {})
        elif country == 'US':
            return self.standards['US_Standards'].get(subject, {})
        else:
            return {}
    
    def get_grade_topics(self, country: str, subject: str, grade: str) -> List[Dict[str, Any]]:
        """
        Get topics for a specific grade level
        
        Args:
            country: 'Ontario' or 'US'
            subject: 'Mathematics' or 'Physics'
            grade: 'Grade_9', 'Grade_10', 'Grade_11', or 'Grade_12'
            
        Returns:
            List of topics for the specified grade
        """
        curriculum = self.get_curriculum_structure(country, subject)
        grade_data = curriculum.get(grade, {})
        
        topics = []
        for course_name, course_data in grade_data.items():
            if 'topics' in course_data:
                for topic in course_data['topics']:
                    topic['course'] = course_name
                    topic['grade'] = grade
                    topic['country'] = country
                    topic['subject'] = subject
                    topics.append(topic)
        
        return topics
    
    def get_all_topics(self) -> List[Dict[str, Any]]:
        """
        Get all topics from all curricula
        
        Returns:
            List of all topics with metadata
        """
        all_topics = []
        
        for country in ['Ontario', 'US']:
            for subject in ['Mathematics', 'Physics']:
                for grade in ['Grade_9', 'Grade_10', 'Grade_11', 'Grade_12']:
                    topics = self.get_grade_topics(country, subject, grade)
                    all_topics.extend(topics)
        
        return all_topics
    
    def find_matching_topics(self, keywords: List[str], country: str = None, 
                           subject: str = None, grade: str = None) -> List[Dict[str, Any]]:
        """
        Find topics that match given keywords
        
        Args:
            keywords: List of keywords to search for
            country: Optional country filter
            subject: Optional subject filter
            grade: Optional grade filter
            
        Returns:
            List of matching topics
        """
        all_topics = self.get_all_topics()
        matching_topics = []
        
        for topic in all_topics:
            # Apply filters
            if country and topic['country'] != country:
                continue
            if subject and topic['subject'] != subject:
                continue
            if grade and topic['grade'] != grade:
                continue
            
            # Check for keyword matches
            topic_text = f"{topic['name']} {' '.join(topic['subtopics'])}".lower()
            
            for keyword in keywords:
                if keyword.lower() in topic_text:
                    matching_topics.append(topic)
                    break
        
        return matching_topics
    
    def export_to_json(self, filename: str = 'enhanced_curriculum_standards.json'):
        """
        Export curriculum standards to JSON file
        
        Args:
            filename: Output filename
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.standards, f, indent=2, ensure_ascii=False)
        print(f"Curriculum standards exported to {filename}")
    
    def generate_classification_prompt_template(self) -> str:
        """
        Generate a template for GPT classification prompts
        
        Returns:
            Template string for classification prompts
        """
        template = """
You are an expert educational content classifier specializing in Ontario and US high school curriculum standards.

CURRICULUM STANDARDS:
{curriculum_standards}

QUESTION TO CLASSIFY:
Title: {title}
Content: {content}
Answer: {answer}
Solution: {solution}
Current Subject: {current_subject}
Current Grade: {current_grade}
Current Difficulty: {current_difficulty}

INSTRUCTIONS:
1. Analyze the question content to determine the most appropriate classification
2. Consider the mathematical/scientific concepts being tested
3. Match to the closest curriculum standard for both Ontario and US
4. Provide confidence scores (0-1) for each classification
5. Consider the difficulty level and grade appropriateness

RESPONSE FORMAT (JSON):
{{
    "ontario_classification": {{
        "grade": "Grade_9|Grade_10|Grade_11|Grade_12",
        "subject": "Mathematics|Physics",
        "course": "specific course name",
        "topic": "specific topic name",
        "subtopic": "specific subtopic",
        "confidence": 0.95,
        "difficulty_level": "beginner|intermediate|advanced|expert"
    }},
    "us_classification": {{
        "grade": "Grade_9|Grade_10|Grade_11|Grade_12",
        "subject": "Mathematics|Physics",
        "course": "specific course name", 
        "topic": "specific topic name",
        "subtopic": "specific subtopic",
        "confidence": 0.95,
        "difficulty_level": "beginner|intermediate|advanced|expert"
    }},
    "reasoning": "Brief explanation of classification decisions",
    "curriculum_alignment": {{
        "ontario_alignment": 0.95,
        "us_alignment": 0.90,
        "notes": "Any special considerations or edge cases"
    }}
}}

Classify this question now:
"""
        return template

def main():
    """
    Demonstrate the enhanced curriculum standards
    """
    standards = EnhancedCurriculumStandards()
    
    print("Enhanced Curriculum Standards Demo")
    print("=" * 50)
    
    # Export to JSON
    standards.export_to_json()
    
    # Demonstrate topic search
    print("\nSearching for 'calculus' topics:")
    calculus_topics = standards.find_matching_topics(['calculus'])
    for topic in calculus_topics[:3]:  # Show first 3
        print(f"  {topic['country']} {topic['grade']} {topic['subject']}: {topic['name']}")
    
    print("\nSearching for 'trigonometry' topics:")
    trig_topics = standards.find_matching_topics(['trigonometry'])
    for topic in trig_topics[:3]:  # Show first 3
        print(f"  {topic['country']} {topic['grade']} {topic['subject']}: {topic['name']}")
    
    # Show curriculum structure
    print("\nOntario Grade 12 Mathematics courses:")
    ontario_math = standards.get_curriculum_structure('Ontario', 'Mathematics')
    grade_12_courses = ontario_math.get('Grade_12', {})
    for course_name in grade_12_courses.keys():
        print(f"  - {course_name}")
    
    print("\nUS Grade 12 Mathematics courses:")
    us_math = standards.get_curriculum_structure('US', 'Mathematics')
    grade_12_courses = us_math.get('Grade_12', {})
    for course_name in grade_12_courses.keys():
        print(f"  - {course_name}")
    
    # Generate prompt template
    template = standards.generate_classification_prompt_template()
    with open('classification_prompt_template.txt', 'w', encoding='utf-8') as f:
        f.write(template)
    print("\nClassification prompt template saved to classification_prompt_template.txt")

if __name__ == '__main__':
    main()
