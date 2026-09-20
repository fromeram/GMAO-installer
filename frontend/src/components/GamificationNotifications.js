// frontend/src/components/GamificationNotifications.js
import React, { useEffect, useState } from 'react';
import { notification, Badge } from 'antd';
import { TrophyOutlined, StarOutlined, GiftOutlined } from '@ant-design/icons';
import { fetchWithAuth } from '../apiConfig';

const GamificationNotifications = () => {
  const [hasNewNotifications, setHasNewNotifications] = useState(false);

  useEffect(() => {
    // Verificar notificaciones al cargar
    checkForNotifications();
    
    // Configurar polling cada 30 segundos
    const interval = setInterval(checkForNotifications, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const checkForNotifications = async () => {
    try {
      const response = await fetchWithAuth('/notifications/gamification');
      
      if (response.new_achievements && response.new_achievements.length > 0) {
        setHasNewNotifications(true);
        
        // Mostrar notificaciones de logros
        response.new_achievements.forEach((achievement, index) => {
          setTimeout(() => {
            showAchievementNotification(achievement);
          }, index * 1000); // Espaciar notificaciones
        });
      }
    } catch (error) {
      console.error('Error checking gamification notifications:', error);
    }
  };

  const showAchievementNotification = (achievement) => {
    const getRarityColor = (rarity) => {
      const colors = {
        common: '#8c8c8c',
        rare: '#1890ff',
        epic: '#722ed1',
        legendary: '#fa8c16'
      };
      return colors[rarity] || '#8c8c8c';
    };

    notification.success({
      message: (
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <TrophyOutlined style={{ color: getRarityColor(achievement.rarity), marginRight: 8 }} />
          <span>¡Nuevo Logro Desbloqueado!</span>
        </div>
      ),
      description: (
        <div>
          <div style={{ fontSize: 16, marginBottom: 4 }}>
            <span style={{ fontSize: 20, marginRight: 8 }}>{achievement.icon}</span>
            <strong>{achievement.name}</strong>
          </div>
          <div style={{ marginBottom: 8 }}>{achievement.description}</div>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <Badge 
              color={getRarityColor(achievement.rarity)} 
              text={achievement.rarity.toUpperCase()}
              style={{ marginRight: 16 }}
            />
            <span style={{ color: '#52c41a', fontWeight: 'bold' }}>
              <GiftOutlined /> +{achievement.points} puntos
            </span>
          </div>
        </div>
      ),
      duration: 6,
      placement: 'topRight',
      style: {
        width: 350,
        backgroundColor: '#f6ffed',
        border: `2px solid ${getRarityColor(achievement.rarity)}`
      }
    });

    // Efecto de sonido (opcional)
    if (achievement.rarity === 'legendary') {
      playSound('achievement-legendary.mp3');
    } else if (achievement.rarity === 'epic') {
      playSound('achievement-epic.mp3');
    } else {
      playSound('achievement.mp3');
    }
  };

  const playSound = (soundFile) => {
    try {
      const audio = new Audio(`/sounds/${soundFile}`);
      audio.volume = 0.3;
      audio.play().catch(e => console.log('No se pudo reproducir sonido:', e));
    } catch (error) {
      console.log('Error reproduciendo sonido:', error);
    }
  };

  return null; // Este componente solo maneja notificaciones
};

// Hook personalizado para usar en otros componentes
export const useGamificationNotifications = () => {
  const [notifications, setNotifications] = useState([]);

  const showPointsGain = (points, reason, bonuses = {}) => {
    notification.info({
      message: (
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <StarOutlined style={{ color: '#faad14', marginRight: 8 }} />
          <span>¡Puntos Ganados!</span>
        </div>
      ),
      description: (
        <div>
          <div style={{ fontSize: 16, fontWeight: 'bold', color: '#52c41a', marginBottom: 4 }}>
            +{points} puntos
          </div>
          <div style={{ marginBottom: 8 }}>{reason}</div>
          {Object.keys(bonuses).length > 0 && (
            <div style={{ fontSize: 12, color: '#666' }}>
              Bonificaciones: {Object.entries(bonuses).map(([key, value]) => 
                `${key}: +${value}`
              ).join(', ')}
            </div>
          )}
        </div>
      ),
      duration: 4,
      placement: 'topRight'
    });
  };

  const showLevelUp = (newLevel) => {
    notification.success({
      message: (
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <StarOutlined style={{ color: '#faad14', marginRight: 8 }} />
          <span>¡Subiste de Nivel!</span>
        </div>
      ),
      description: (
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 24, marginBottom: 8 }}>🎉</div>
          <div style={{ fontSize: 18, fontWeight: 'bold' }}>
            ¡Ahora eres Nivel {newLevel}!
          </div>
        </div>
      ),
      duration: 6,
      placement: 'topRight',
      style: {
        backgroundColor: '#fff7e6',
        border: '2px solid #faad14'
      }
    });
    
    playSound('level-up.mp3');
  };

  return {
    showPointsGain,
    showLevelUp
  };
};

export default GamificationNotifications;