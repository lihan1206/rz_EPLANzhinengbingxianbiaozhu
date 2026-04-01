import { useMemo, type ReactNode } from 'react';
import {
  ApartmentOutlined,
  BarChartOutlined,
  FileTextOutlined,
  LoginOutlined,
  ProjectOutlined,
  TeamOutlined,
  UploadOutlined,
  FunctionOutlined,
} from '@ant-design/icons';
import { Button, Layout, Menu, Select, Space, Typography } from 'antd';
import { useLocation, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';

import { getProjects } from '../api/services';
import { useAppContext } from './AppContext';
import { clearToken } from '../utils/storage';

const { Header, Content, Sider } = Layout;

const menuItems = [
  { key: '/', icon: <BarChartOutlined />, label: '总览面板' },
  { key: '/projects', icon: <ProjectOutlined />, label: '项目管理' },
  { key: '/imports', icon: <UploadOutlined />, label: '数据导入' },
  { key: '/analysis', icon: <ApartmentOutlined />, label: '并线分析' },
  { key: '/annotations', icon: <FileTextOutlined />, label: '自动标注' },
  { key: '/wire-analysis', icon: <FunctionOutlined />, label: '导线分析工具' },
  { key: '/users', icon: <TeamOutlined />, label: '用户与日志' },
];

export const MainLayout = ({ children }: { children: ReactNode }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { selectedProjectId, setSelectedProjectId } = useAppContext();

  const { data: projects = [] } = useQuery({
    queryKey: ['projects', 'layout'],
    queryFn: getProjects,
  });

  const selectedMenuKey = useMemo(() => {
    const found = menuItems.find((item) => item.key === location.pathname);
    return found ? [found.key] : ['/'];
  }, [location.pathname]);

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider breakpoint="lg" collapsedWidth={80} className="app-sider">
        <div className="brand-box">
          <Typography.Title level={5} style={{ margin: 0, color: '#e6f4ff' }}>
            EPLAN智能并线标注系统
          </Typography.Title>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={selectedMenuKey}
          items={menuItems}
          onClick={(item) => navigate(item.key)}
        />
      </Sider>
      <Layout>
        <Header className="app-header">
          <Space style={{ width: '100%', justifyContent: 'space-between' }}>
            <Typography.Text strong style={{ color: '#11304a' }}>
              电气设计并线智能标注工作台
            </Typography.Text>
            <Space>
              <Select
                allowClear
                placeholder="请选择当前项目"
                style={{ width: 260 }}
                value={selectedProjectId}
                options={projects.map((project) => ({
                  label: `${project.name} (${project.version})`,
                  value: project.id,
                }))}
                onChange={(value) => setSelectedProjectId(value)}
              />
              <Button
                icon={<LoginOutlined />}
                onClick={() => {
                  clearToken();
                  navigate('/login');
                }}
              >
                退出登录
              </Button>
            </Space>
          </Space>
        </Header>
        <Content className="app-content">{children}</Content>
      </Layout>
    </Layout>
  );
};
