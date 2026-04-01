import React, { useState } from 'react';
import { Button, Card, Col, InputNumber, Row, Table, Tag, message } from 'antd';
import TextArea from 'antd/es/input/TextArea';
import { analyzeWires } from '../api/services';
import { ParallelGroupOutput, WireAnalysisResponse } from '../types';

const WireAnalysisPage: React.FC = () => {
  const [jsonInput, setJsonInput] = useState<string>(`{
  "wires": [
    {"id": "W001", "start": "X1:1", "end": "X2:1", "area": 2.5, "color": "红色", "properties": {"电压等级": "220V", "屏蔽": "否"}},
    {"id": "W002", "start": "X1:1", "end": "X2:1", "area": 2.5, "color": "红色", "properties": {"电压等级": "220V", "屏蔽": "否"}},
    {"id": "W003", "start": "X1:1", "end": "X2:1", "area": 2.5, "color": "红色", "properties": {"电压等级": "220V", "屏蔽": "否"}},
    {"id": "W004", "start": "X1:2", "end": "X3:1", "area": 1.5, "color": "蓝色", "properties": {"电压等级": "24V", "屏蔽": "是"}},
    {"id": "W005", "start": "X1:2", "end": "X3:1", "area": 1.5, "color": "蓝色", "properties": {"电压等级": "24V", "屏蔽": "是"}},
    {"id": "W006", "start": "X1:3", "end": "X4:1", "area": 4, "color": "黄色", "properties": {"电压等级": "380V", "屏蔽": "否"}},
    {"id": "W007", "start": "X1:4", "end": "X5:1", "area": 2.5, "color": "绿色", "properties": {"电压等级": "220V", "屏蔽": "否"}}
  ],
  "min_parallel_count": 2,
  "max_parallel_count": 4
}`);
  const [result, setResult] = useState<WireAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [minCount, setMinCount] = useState(2);
  const [maxCount, setMaxCount] = useState(4);

  const handleAnalyze = async () => {
    try {
      setLoading(true);
      const inputData = JSON.parse(jsonInput);
      
      const payload = {
        ...inputData,
        min_parallel_count: minCount,
        max_parallel_count: maxCount,
      };

      const response = await analyzeWires(payload);
      setResult(response);
      message.success(`分析完成，发现 ${response.total_groups} 个并线组`);
    } catch (error: any) {
      message.error(error.response?.data?.detail || '分析失败，请检查输入格式');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    {
      title: '并线组ID',
      dataIndex: 'parallel_group_id',
      key: 'parallel_group_id',
      width: 100,
    },
    {
      title: '数量',
      dataIndex: 'count',
      key: 'count',
      width: 80,
    },
    {
      title: '总截面积(mm²)',
      dataIndex: 'total_area',
      key: 'total_area',
      width: 120,
    },
    {
      title: '起点',
      dataIndex: 'start',
      key: 'start',
      width: 100,
    },
    {
      title: '终点',
      dataIndex: 'end',
      key: 'end',
      width: 100,
    },
    {
      title: '标注文本',
      dataIndex: 'label',
      key: 'label',
      width: 150,
    },
    {
      title: '合规性',
      dataIndex: 'compliant',
      key: 'compliant',
      width: 100,
      render: (compliant: boolean) => (
        <Tag color={compliant ? 'green' : 'red'}>
          {compliant ? '合规' : '不合规'}
        </Tag>
      ),
    },
    {
      title: '判断依据',
      dataIndex: 'notes',
      key: 'notes',
      render: (notes: string[]) => (
        <ul className="list-disc list-inside text-sm">
          {notes.map((note, index) => (
            <li key={index}>{note}</li>
          ))}
        </ul>
      ),
    },
  ];

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">EPLAN 导线并线智能标注工具</h1>
      
      <Row gutter={16}>
        <Col span={12}>
          <Card title="输入配置" className="mb-4">
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">最小并线数量</label>
              <InputNumber
                min={2}
                max={10}
                value={minCount}
                onChange={(value) => setMinCount(value || 2)}
                className="w-full"
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">最大并线数量</label>
              <InputNumber
                min={2}
                max={20}
                value={maxCount}
                onChange={(value) => setMaxCount(value || 4)}
                className="w-full"
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">导线数据 (JSON格式)</label>
              <TextArea
                value={jsonInput}
                onChange={(e) => setJsonInput(e.target.value)}
                rows={15}
                className="font-mono text-sm"
              />
            </div>
            <Button
              type="primary"
              onClick={handleAnalyze}
              loading={loading}
              className="w-full"
              size="large"
            >
              开始分析
            </Button>
          </Card>
        </Col>
        
        <Col span={12}>
          <Card 
            title="分析结果" 
            extra={result && <span>共 {result.total_groups} 个并线组，{result.total_wires_analyzed} 根导线</span>}
          >
            {result ? (
              <>
                <Table
                  dataSource={result.parallel_groups}
                  columns={columns}
                  rowKey="parallel_group_id"
                  pagination={false}
                  bordered
                  size="small"
                  scroll={{ y: 400 }}
                />
                <div className="mt-4">
                  <h3 className="font-medium mb-2">JSON 输出:</h3>
                  <pre className="bg-gray-100 p-3 rounded text-xs overflow-auto max-h-48">
                    {JSON.stringify(result, null, 2)}
                  </pre>
                </div>
              </>
            ) : (
              <div className="text-center text-gray-500 py-12">
                请点击"开始分析"按钮查看结果
              </div>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default WireAnalysisPage;
