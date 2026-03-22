const bcrypt = require('bcrypt');
const compression = require('compression');
const express = require('express');
const http = require('http'); // 必须加在最前面！
const cors = require('cors');
const pool = require('./config/db');
require('dotenv').config();
const axios = require('axios');
const WebSocket = require('ws');

const app = express();
app.use(compression());
app.use(cors());
// 解析JSON请求体
app.use(express.json());
// 解析表单格式请求体（兼容更多场景）
app.use(express.urlencoded({ extended: true }));

// ===================== 基础测试接口 =====================
app.get('/test-db', async (req, res) => {
  try {
    const conn = await pool.getConnection();
    conn.release();
    res.json({ code: 200, message: '数据库连接成功！' });
  } catch (err) {
    res.status(500).json({ code: 500, message: '数据库连接失败', error: err.message });
  }
});

// ===================== 用户相关接口（第5天新增完善） =====================
/**
 * 1. 用户注册
 * 请求方式：POST
 * 请求地址：/api/user/register
 * 请求参数：{ "username": "test", "password": "123456" }
 */
app.post('/api/user/register', async (req, res) => {
  try {
    const { username, password } = req.body;
    // 1. 保留你原来的参数校验、查重复用户逻辑
    if (!username || !password) {
      return res.json({ code: 400, message: '用户名和密码不能为空' });
    }
    const [existingUser] = await pool.query('SELECT * FROM user WHERE username = ?', [username]);
    if (existingUser.length > 0) {
      return res.json({ code: 400, message: '用户名已存在' });
    }
    // 2. 新增：密码哈希（核心替换点）
    const saltRounds = 10;
    const passwordHash = await bcrypt.hash(password, saltRounds);
    // 3. 替换：存哈希值，而不是明文password
    await pool.query('INSERT INTO user (username, password) VALUES (?, ?)', [username, passwordHash]);
    res.json({ code: 200, message: '注册成功' });
  } catch (err) {
    console.error('注册失败：', err);
    res.json({ code: 500, message: '服务器错误' });
  }
});/**
 * 2. 用户登录
 * 请求方式：POST
 * 请求地址：/api/user/login
 * 请求参数：{ "username": "test", "password": "123456" }
 */
// 登录接口（哈希验证版）
app.post('/api/user/login', async (req, res) => {
  try {
    const { username, password } = req.body;
    if (!username || !password) {
      return res.json({ code: 400, message: '用户名和密码不能为空' });
    }
    const [userList] = await pool.query('SELECT * FROM user WHERE username = ? LIMIT 1', [username]);
    if (userList.length === 0) {
      return res.json({ code: 400, message: '用户名或密码错误' });
    }
    const user = userList[0];
    // 核心替换：用 bcrypt.compare 对比，而不是直接判断 password === user.password
    const isPwdRight = await bcrypt.compare(password, user.password);
    if (!isPwdRight) {
      return res.json({ code: 400, message: '用户名或密码错误' });
    }
    res.json({
      code: 200,
      message: '登录成功',
      data: { id: user.id, username: user.username }
    });
  } catch (err) {
    console.error('登录失败：', err);
    res.json({ code: 500, message: '服务器错误' });
  }
});/**
 * 3. 删除用户
 * 请求方式：DELETE
 * 请求地址：/api/user/:id
 * 示例：/api/user/1（删除ID为1的用户）
 */
app.delete('/api/user/:id', async (req, res) => {
  try {
    const { id } = req.params;
    // 校验ID是否为数字
    if (isNaN(id)) {
      return res.status(400).json({ code: 400, message: '用户ID必须是数字！' });
    }
    // 执行删除
    const [result] = await pool.query('DELETE FROM user WHERE id = ?', [id]);
    if (result.affectedRows === 0) {
      return res.status(404).json({ code: 404, message: '用户不存在！' });
    }
    res.json({ code: 200, message: '删除用户成功！' });
  } catch (e) {
    res.status(500).json({ code: 500, message: '删除用户失败', error: e.message });
  }
});

// ===================== 笔记相关接口（第5天新增完善） =====================
/**
 * 1. 获取所有笔记
 * 请求方式：GET
 * 请求地址：/api/note
 */
app.get('/api/note', async (req, res) => {
  try {
    const [rows] = await pool.query('SELECT * FROM note ORDER BY create_time DESC');
    res.json({ code: 200, message: '获取笔记成功！', data: rows });
  } catch (e) {
    res.status(500).json({ code: 500, message: '获取笔记失败', error: e.message });
  }
});

/**
 * 2. 获取单条笔记
 * 请求方式：GET
 * 请求地址：/api/note/:id
 * 示例：/api/note/1（获取ID为1的笔记）
 */
app.get('/api/note/:id', async (req, res) => {
  try {
    const { id } = req.params;
    if (isNaN(id)) {
      return res.status(400).json({ code: 400, message: '笔记ID必须是数字！' });
    }
    const [rows] = await pool.query('SELECT * FROM note WHERE id = ?', [id]);
    if (rows.length === 0) {
      return res.status(404).json({ code: 404, message: '笔记不存在！' });
    }
    res.json({ code: 200, message: '获取笔记成功！', data: rows[0] });
  } catch (e) {
    res.status(500).json({ code: 500, message: '获取笔记失败', error: e.message });
  }
});

/**
 * 3. 添加笔记
 * 请求方式：POST
 * 请求地址：/api/note
 * 请求参数：{ "content": "这是一条新笔记" }
 */
app.post('/api/note', async (req, res) => {
  try {
    const { content } = req.body;
    if (!content || content.trim() === '') {
      return res.status(400).json({ code: 400, message: '笔记内容不能为空！' });
    }
    await pool.query('INSERT INTO note (content) VALUES (?)', [content.trim()]);
    res.json({ code: 200, message: '添加笔记成功！' });
  } catch (e) {
    res.status(500).json({ code: 500, message: '添加笔记失败', error: e.message });
  }
});

/**
 * 4. 修改笔记
 * 请求方式：PUT
 * 请求地址：/api/note/:id
 * 请求参数：{ "content": "修改后的笔记内容" }
 * 示例：/api/note/1（修改ID为1的笔记）
 */
app.put('/api/note/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { content } = req.body;
    if (isNaN(id)) {
      return res.status(400).json({ code: 400, message: '笔记ID必须是数字！' });
    }
    if (!content || content.trim() === '') {
      return res.status(400).json({ code: 400, message: '笔记内容不能为空！' });
    }
    // 先检查笔记是否存在
    const [rows] = await pool.query('SELECT * FROM note WHERE id = ?', [id]);
    if (rows.length === 0) {
      return res.status(404).json({ code: 404, message: '笔记不存在！' });
    }
    // 执行修改
    await pool.query('UPDATE note SET content = ? WHERE id = ?', [content.trim(), id]);
    res.json({ code: 200, message: '修改笔记成功！' });
  } catch (e) {
    res.status(500).json({ code: 500, message: '修改笔记失败', error: e.message });
  }
});

/**
 * 5. 删除笔记
 * 请求方式：DELETE
 * 请求地址：/api/note/:id
 * 示例：/api/note/1（删除ID为1的笔记）
 */
app.delete('/api/note/:id', async (req, res) => {
  try {
    const { id } = req.params;
    if (isNaN(id)) {
      return res.status(400).json({ code: 400, message: '笔记ID必须是数字！' });
    }
    const [result] = await pool.query('DELETE FROM note WHERE id = ?', [id]);
    if (result.affectedRows === 0) {
      return res.status(404).json({ code: 404, message: '笔记不存在！' });
    }
    res.json({ code: 200, message: '删除笔记成功！' });
  } catch (e) {
    res.status(500).json({ code: 500, message: '删除笔记失败', error: e.message });
  }
});

// ===================== 启动服务 =====================
// 启动服务
// ====================== 创建 HTTP 服务器 ======================
const server = http.createServer(app);

// ====================== 创建 WebSocket 服务器 ======================
const wss = new WebSocket.Server({ server });

// 监听 WebSocket 连接
wss.on('connection', (ws) => {
  console.log("✅ 新客户端连接 WebSocket");

  ws.on('message', (data) => {
    const message = data.toString();
    console.log("📩 收到客户端消息：", message);
    // 广播给所有客户端
    wss.clients.forEach((client) => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(message);
      }
    });
  });

  ws.on('close', () => {
    console.log("❌ 客户端断开 WebSocket 连接");
  });
});

// ====================== 启动服务（HTTP + WebSocket） ======================
const PORT = process.env.PORT || 3000;
server.listen(PORT, '0.0.0.0', () => {
  console.log(`✅ 服务已启动，访问地址：http://0.0.0.0:${PORT}`);
  console.log(`✅ WebSocket 服务器已启动，可实时通信`);
});// ====================== 第二周：对话接口 ======================
// 1. 新增对话 + AI 旅行生成
app.post('/api/chat', async (req, res) => {
  try {
    const { user_id, content } = req.body;

    if (!user_id || !content) {
      return res.status(400).json({
        code: 400,
        message: '用户ID和对话内容不能为空',
        data: null
      });
    }

    // 先把消息存进数据库
    await pool.query(
      'INSERT INTO chat (user_id, content) VALUES (?, ?)',
      [user_id, content]
    );

    // ====================== 调用 AI 接口 ======================
    let aiData = null;
    try {
      const aiResponse = await axios({
        method: 'POST',
        url: 'http://10.33.31.149:5000/api/ai/travel/linkage',
        headers: {
          'Content-Type': 'application/json'
        },
        data: {
          user_input: content
        }
      });
      aiData = aiResponse.data;
    } catch (err) {
      console.log("AI接口调用失败，但消息已保存");
    }
// ====================== 解析 AI 返回的多日行程数据 ======================
let formattedItinerary = [];
if (aiData && aiData.data && aiData.data.daily_itinerary) {
  formattedItinerary = aiData.data.daily_itinerary.map(day => {
    return {
      day: day.day,
      poi_list: day.itinerary.poi_list,
      routes: day.itinerary.routes,
      total_distance: day.itinerary.total_distance,
      total_duration: day.itinerary.total_duration
    };
  });
}
    // 返回给前端：聊天成功 + AI结果
  res.json({
  code: 200,
  message: "发送对话成功",
  data: {
    ai_result: aiData,
    daily_itinerary: formattedItinerary
  }
});

  } catch (e) {
    res.status(500).json({ code: 500, message: '发送失败', data: null });
  }
});
// 2. 获取某个用户的所有对话
app.get('/api/chat/list/:user_id', async (req, res) => {
  try {
    const { user_id } = req.params;
    const [chats] = await pool.query(
      'SELECT * FROM chat WHERE user_id = ? ORDER BY id ASC',
      [user_id]
    );
    res.json({ code: 200, message: '获取对话成功', data: chats });
  } catch (e) {
    res.status(500).json({ code: 500, message: '获取失败', data: null });
  }
});

// 3. 获取单条对话
app.get('/api/chat/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const [chats] = await pool.query(
      'SELECT * FROM chat WHERE id = ?',
      [id]
    );
    if (chats.length === 0) {
      return res.status(400).json({ code: 400, message: '对话不存在', data: null });
    }
    res.json({ code: 200, message: '获取成功', data: chats[0] });
  } catch (e) {
    res.status(500).json({ code: 500, message: '获取失败', data: null });
  }
});

// 4. 删除对话
app.delete('/api/chat/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { user_id } = req.body;

    const [result] = await pool.query(
      'DELETE FROM chat WHERE id = ? AND user_id = ?',
      [id, user_id]
    );

    if (result.affectedRows === 0) {
      return res.status(400).json({ code: 400, message: '删除失败或无权限', data: null });
    }

    res.json({ code: 200, message: '删除对话成功', data: null });
  } catch (e) {
    res.status(500).json({ code: 500, message: '删除失败', data: null });
  }
});
// ====================== 第三周：行程生成接口 ======================

// 1. 创建行程（核心：生成接口）
app.post('/api/itinerary/generate', async (req, res) => {
  try {
    const { user_id, title, start_time, end_time, destination, description } = req.body;

    // 基础参数校验
    if (!user_id || !title || !start_time || !end_time || !destination) {
      return res.status(400).json({
        code: 400,
        message: '用户ID、标题、起止时间、目的地不能为空',
        data: null
      });
    }

    // 写入数据库（当前版本：直接保存，后续可对接AI生成逻辑）
    await pool.query(
      'INSERT INTO itinerary (user_id, title, start_time, end_time, destination, description) VALUES (?, ?, ?, ?, ?, ?)',
      [user_id, title, start_time, end_time, destination, description || '']
    );

    res.json({
      code: 200,
      message: '行程生成成功',
      data: {
        user_id,
        title,
        start_time,
        end_time,
        destination,
        description
      }
    });
  } catch (e) {
    res.status(500).json({ code: 500, message: '行程生成失败', data: null });
  }
});

// 2. 获取用户的所有行程
app.get('/api/itinerary/list/:user_id', async (req, res) => {
  try {
    const { user_id } = req.params;
    const [itineraries] = await pool.query(
      'SELECT * FROM itinerary WHERE user_id = ? ORDER BY start_time ASC',
      [user_id]
    );
    res.json({ code: 200, message: '获取行程成功', data: itineraries });
  } catch (e) {
    res.status(500).json({ code: 500, message: '获取行程失败', data: null });
  }
});

// 3. 获取单条行程详情
app.get('/api/itinerary/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const [itineraries] = await pool.query('SELECT * FROM itinerary WHERE id = ?', [id]);
    if (itineraries.length === 0) {
      return res.status(400).json({ code: 400, message: '行程不存在', data: null });
    }
    res.json({ code: 200, message: '获取行程成功', data: itineraries[0] });
  } catch (e) {
    res.status(500).json({ code: 500, message: '获取行程失败', data: null });
  }
});

// 4. 删除行程（只能删自己的）
app.delete('/api/itinerary/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { user_id } = req.body;
    const [result] = await pool.query(
      'DELETE FROM itinerary WHERE id = ? AND user_id = ?',
      [id, user_id]
    );
    if (result.affectedRows === 0) {
      return res.status(400).json({ code: 400, message: '删除失败，无权限或行程不存在', data: null });
    }
    res.json({ code: 200, message: '删除行程成功', data: null });
  } catch (e) {
    res.status(500).json({ code: 500, message: '删除行程失败', data: null });
  }
});
// 获取用户历史行程接口（第五周任务）
app.get('/api/itinerary', async (req, res) => {
  try {
    const { user_id } = req.query;

    // 校验参数
    if (!user_id) {
      return res.status(400).json({
        code: 400,
        message: 'user_id 不能为空',
        data: null
      });
    }

    // 从数据库查询该用户的所有行程，按 day 升序排列
    const [rows] = await pool.query(
      'SELECT * FROM itinerary WHERE user_id = ? ORDER BY day ASC',
      [user_id]
    );

    // 把 JSON 字符串转回对象，方便前端使用
    const formattedData = rows.map(row => ({
      id: row.id,
      user_id: row.user_id,
      day: row.day,
      poi_list: JSON.parse(row.poi_list),
      routes: JSON.parse(row.routes),
      total_distance: row.total_distance,
      total_duration: row.total_duration,
      created_at: row.created_at
    }));

    res.json({
      code: 200,
      message: '获取历史行程成功',
      data: formattedData
    });

  } catch (err) {
    console.error('获取历史行程失败:', err);
    res.status(500).json({
      code: 500,
      message: '服务器错误',
      data: null
    });
  }
});
