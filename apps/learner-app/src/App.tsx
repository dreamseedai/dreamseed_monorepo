import { useState, useEffect } from 'react'
import { Button, Card } from '@dreamseed/shared-ui'
import type { LearningModule } from '@dreamseed/shared-types'
import './App.css'

// Mock learning modules data
const mockModules: LearningModule[] = [
  {
    id: "1",
    title: "Introduction to React",
    description: "Learn the basics of React components and JSX",
    content: "React is a JavaScript library for building user interfaces...",
    type: "article",
    duration: 45,
    difficulty: "beginner",
    tags: ["javascript", "react", "frontend"]
  },
  {
    id: "2", 
    title: "Python Data Structures",
    description: "Master lists, dictionaries, and sets in Python",
    content: "Python provides several built-in data structures...",
    type: "video",
    duration: 60,
    difficulty: "beginner",
    tags: ["python", "data-structures", "programming"]
  },
  {
    id: "3",
    title: "Docker Fundamentals", 
    description: "Learn containerization with Docker",
    content: "Docker is a platform for developing, shipping, and running applications...",
    type: "exercise",
    duration: 90,
    difficulty: "intermediate",
    tags: ["docker", "devops", "containers"]
  }
]

function App() {
  const [modules, setModules] = useState<LearningModule[]>([])
  const [selectedModule, setSelectedModule] = useState<LearningModule | null>(null)
  const [progress, setProgress] = useState<Record<string, number>>({})

  useEffect(() => {
    // Simulate API call
    setModules(mockModules)
  }, [])

  const startModule = (module: LearningModule) => {
    setSelectedModule(module)
    if (!progress[module.id]) {
      setProgress(prev => ({ ...prev, [module.id]: 0 }))
    }
  }

  const updateProgress = (moduleId: string, newProgress: number) => {
    setProgress(prev => ({ ...prev, [moduleId]: newProgress }))
  }

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return 'bg-green-100 text-green-800'
      case 'intermediate': return 'bg-yellow-100 text-yellow-800'
      case 'advanced': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'video': return '📹'
      case 'article': return '📄'
      case 'exercise': return '💻'
      case 'quiz': return '❓'
      default: return '📚'
    }
  }

  if (selectedModule) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4">
          <div className="mb-6">
            <Button 
              variant="secondary" 
              onClick={() => setSelectedModule(null)}
            >
              ← Back to Modules
            </Button>
          </div>
          
          <Card title={selectedModule.title}>
            <div className="space-y-4">
              <div className="flex items-center gap-4 text-sm text-gray-600">
                <span>{getTypeIcon(selectedModule.type)} {selectedModule.type}</span>
                <span>⏱️ {selectedModule.duration} minutes</span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(selectedModule.difficulty)}`}>
                  {selectedModule.difficulty}
                </span>
              </div>
              
              <p className="text-gray-700">{selectedModule.description}</p>
              
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="font-medium mb-2">Content</h3>
                <p className="text-gray-700">{selectedModule.content}</p>
              </div>
              
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">Progress:</span>
                <div className="flex-1 bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${progress[selectedModule.id] || 0}%` }}
                  ></div>
                </div>
                <span className="text-sm text-gray-600">{progress[selectedModule.id] || 0}%</span>
              </div>
              
              <div className="flex gap-2">
                <Button onClick={() => updateProgress(selectedModule.id, Math.min((progress[selectedModule.id] || 0) + 25, 100))}>
                  Mark Progress (+25%)
                </Button>
                {progress[selectedModule.id] === 100 && (
                  <Button variant="secondary">
                    ✅ Completed
                  </Button>
                )}
              </div>
            </div>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            DreamSeed Learner
          </h1>
          <p className="text-xl text-gray-600">
            Your personalized learning experience
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {modules.map((module) => (
            <Card key={module.id} className="hover:shadow-lg transition-shadow">
              <div className="space-y-4">
                <div className="flex items-start justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">{module.title}</h3>
                  <span className="text-2xl">{getTypeIcon(module.type)}</span>
                </div>
                
                <p className="text-gray-600 text-sm">{module.description}</p>
                
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <span>⏱️ {module.duration}min</span>
                  <span className={`px-2 py-1 rounded-full font-medium ${getDifficultyColor(module.difficulty)}`}>
                    {module.difficulty}
                  </span>
                </div>
                
                <div className="flex flex-wrap gap-1">
                  {module.tags.map((tag) => (
                    <span key={tag} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                      {tag}
                    </span>
                  ))}
                </div>
                
                {progress[module.id] > 0 && (
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${progress[module.id]}%` }}
                      ></div>
                    </div>
                    <span className="text-xs text-gray-600">{progress[module.id]}%</span>
                  </div>
                )}
                
                <Button 
                  onClick={() => startModule(module)}
                  className="w-full"
                >
                  {progress[module.id] > 0 ? 'Continue' : 'Start Learning'}
                </Button>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}

export default App
