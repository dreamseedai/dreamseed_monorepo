import React from 'react';
import Header from '../../components/Header';

export default function USExamsAdmissions() {
  return (
    <div>
      <Header />
      <div className="max-w-6xl mx-auto px-4 py-8">
        <h2 className="text-2xl font-bold mb-4">Exams & Admissions</h2>
        <p className="text-gray-600 mb-6">SAT/AP/ACT 및 입시 절차(OUAC 등) 대비 리소스와 가이드를 확인하세요.</p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <a href="/guides/us/exams/sat" className="border rounded-xl p-4 hover:shadow-md transition">
            <h3 className="font-semibold mb-1">SAT 대비</h3>
            <div className="text-sm text-gray-600">점수대별 전략, 추천 학습 경로</div>
          </a>
          <a href="/guides/us/exams/ap" className="border rounded-xl p-4 hover:shadow-md transition">
            <h3 className="font-semibold mb-1">AP 대비</h3>
            <div className="text-sm text-gray-600">과목 선택, 난이도, 학습 로드맵</div>
          </a>
          <a href="/guides/us/exams/act" className="border rounded-xl p-4 hover:shadow-md transition">
            <h3 className="font-semibold mb-1">ACT 대비</h3>
            <div className="text-sm text-gray-600">영역별 전략과 시간 관리</div>
          </a>
          <a href="/guides/us/exams/ouac" className="border rounded-xl p-4 hover:shadow-md transition">
            <h3 className="font-semibold mb-1">OUAC 가이드</h3>
            <div className="text-sm text-gray-600">캐나다 온타리오 지원 절차 개요</div>
          </a>
        </div>
      </div>
    </div>
  );
}


