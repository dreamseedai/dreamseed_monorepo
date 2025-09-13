import { useState } from 'react'
import { OnboardingFormComponent } from './components/OnboardingForm'
import type { OnboardingForm } from '@dreamseed/shared-types'
import './App.css'

function App() {
  const [isOnboardingComplete, setIsOnboardingComplete] = useState(false)
  const [userData, setUserData] = useState<OnboardingForm | null>(null)

  const handleOnboardingSubmit = (data: OnboardingForm) => {
    console.log('Onboarding data:', data)
    setUserData(data)
    setIsOnboardingComplete(true)
    // In a real app, this would send data to the backend
  }

  if (!isOnboardingComplete) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              DreamSeed Portal V2
            </h1>
            <p className="text-xl text-gray-600">
              Your AI-powered learning journey starts here
            </p>
          </div>
          <OnboardingFormComponent onSubmit={handleOnboardingSubmit} />
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Welcome, {userData?.firstName}!
          </h1>
          <p className="text-xl text-gray-600">
            Your learning dashboard is ready
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Career Goals</h2>
            <ul className="space-y-2">
              {userData?.careerGoals.map((goal, index) => (
                <li key={index} className="text-gray-700">• {goal}</li>
              ))}
            </ul>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Learning Style</h2>
            <p className="text-gray-700">
              <strong>Pace:</strong> {userData?.learningPreferences.preferredPace}
            </p>
            <p className="text-gray-700">
              <strong>Style:</strong> {userData?.learningPreferences.learningStyle}
            </p>
            <p className="text-gray-700">
              <strong>Time:</strong> {userData?.learningPreferences.timeCommitment}
            </p>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Technical Level</h2>
            <p className="text-gray-700 capitalize">
              {userData?.technicalBackground}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
