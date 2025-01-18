// src/components/custom/StatsGrid.js
"use client";
import { Card, CardContent } from '@/components/ui/card';
import { BarChart, Image, TrendingDown, Scale } from 'lucide-react';

export default function StatsGrid({ stats }) {
  const statsItems = [
    { 
      title: 'Total Files',
      value: stats.totalFiles,
      suffix: '',
      Icon: Image,
      color: 'text-blue-400'
    },
    { 
      title: 'Total Size',
      value: stats.totalSize,
      suffix: '',
      Icon: Scale,
      color: 'text-green-400'
    },
    { 
      title: 'Optimized',
      value: stats.optimizedSize,
      suffix: '',
      Icon: BarChart,
      color: 'text-purple-400'
    },
    { 
      title: 'Reduction',
      value: stats.reduction,
      suffix: '',
      Icon: TrendingDown,
      color: 'text-indigo-400'
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {statsItems.map((stat) => (
        <Card key={stat.title} className="bg-slate-800/50 border-slate-700 overflow-hidden">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-400">
                  {stat.title}
                </p>
                <p className="mt-2 text-3xl font-semibold text-white">
                  {stat.value}{stat.suffix}
                </p>
              </div>
              <div className={`p-3 rounded-xl bg-slate-700/50 ${stat.color}`}>
                <stat.Icon className="w-6 h-6" />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}