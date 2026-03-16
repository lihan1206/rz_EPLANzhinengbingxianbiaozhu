import { LockOutlined, UserOutlined } from '@ant-design/icons';
import { Button, Card, Form, Input, Space, Typography, notification } from 'antd';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';

import { login } from '../api/services';
import { setToken } from '../utils/storage';

const schema = z.object({
  username: z.string().min(3, '用户名至少 3 位'),
  password: z.string().min(6, '密码至少 6 位'),
});

type FormValues = z.infer<typeof schema>;

export const LoginPage = () => {
  const navigate = useNavigate();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      username: 'admin',
      password: 'admin123',
    },
  });

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: (data) => {
      setToken(data.access_token);
      notification.success({ message: '登录成功', description: '欢迎进入智能并线标注系统' });
      navigate('/');
    },
    onError: (error: any) => {
      notification.error({
        message: '登录失败',
        description: error?.response?.data?.detail || '请检查账号或密码后重试',
      });
    },
  });

  const onSubmit = (values: FormValues) => {
    loginMutation.mutate(values);
  };

  return (
    <div className="login-page">
      <Card className="login-card" bordered={false}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Typography.Title level={3} style={{ marginBottom: 8 }}>
              EPLAN智能并线标注系统
            </Typography.Title>
            <Typography.Text type="secondary">请输入账号信息后登录系统</Typography.Text>
          </div>

          <Form layout="vertical" onFinish={handleSubmit(onSubmit)}>
            <Form.Item
              label="用户名"
              validateStatus={errors.username ? 'error' : ''}
              help={errors.username?.message}
            >
              <Input prefix={<UserOutlined />} placeholder="请输入用户名" {...register('username')} />
            </Form.Item>
            <Form.Item
              label="密码"
              validateStatus={errors.password ? 'error' : ''}
              help={errors.password?.message}
            >
              <Input.Password prefix={<LockOutlined />} placeholder="请输入密码" {...register('password')} />
            </Form.Item>
            <Button type="primary" htmlType="submit" block loading={loginMutation.isPending}>
              登录系统
            </Button>
          </Form>

          <Typography.Text type="secondary">演示账号：admin / admin123</Typography.Text>
        </Space>
      </Card>
    </div>
  );
};
