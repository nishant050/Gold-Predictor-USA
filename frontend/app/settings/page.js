'use client';
import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import styles from './settings.module.css';

const PROVIDERS = [
  { id: 'goldapi', name: 'GoldAPI.io' },
  { id: 'fred', name: 'Federal Reserve (FRED)' },
  { id: 'newsapi', name: 'NewsAPI.org' },
  { id: 'openrouter', name: 'OpenRouter (LLMs)' }
];

const DEFAULT_OPENROUTER_MODEL = 'poolside/laguna-m.1:free';
const OPENROUTER_MODEL_OPTIONS = [
  'poolside/laguna-m.1:free',
  'anthropic/claude-3.5-sonnet',
  'google/gemini-2.5-flash',
  'openai/gpt-4o-mini',
  'meta-llama/llama-3.1-8b-instruct:free'
];

export default function SettingsPage() {
  const [keys, setKeys] = useState({});
  const [loading, setLoading] = useState(true);
  const [newKeyValues, setNewKeyValues] = useState({});
  const [openrouterModel, setOpenrouterModel] = useState(DEFAULT_OPENROUTER_MODEL);
  const [modelSaving, setModelSaving] = useState(false);
  const [modelSaved, setModelSaved] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const [keysData, modelSetting] = await Promise.all([
        api.getApiKeys(),
        api.getSetting('openrouter_model')
      ]);
      setKeys(keysData);
      setOpenrouterModel(modelSetting.value || DEFAULT_OPENROUTER_MODEL);
    } catch (err) {
      console.error('Failed to fetch settings:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchKeys = async () => {
    try {
      const data = await api.getApiKeys();
      setKeys(data);
    } catch (err) {
      console.error('Failed to fetch keys:', err);
    }
  };

  const handleAddKey = async (provider) => {
    const val = newKeyValues[provider];
    if (!val || !val.trim()) return;

    try {
      await api.addApiKey(provider, val.trim());
      setNewKeyValues({ ...newKeyValues, [provider]: '' });
      fetchKeys();
    } catch (err) {
      alert('Error adding key: ' + err.message);
    }
  };

  const handleDelete = async (keyId) => {
    if (!confirm('Delete this API key?')) return;
    try {
      await api.deleteApiKey(keyId);
      fetchKeys();
    } catch (err) {
      alert('Error deleting key: ' + err.message);
    }
  };

  const handleReactivate = async (keyId) => {
    try {
      await api.reactivateApiKey(keyId);
      fetchKeys();
    } catch (err) {
      alert('Error reactivating key: ' + err.message);
    }
  };

  const handleSaveModel = async () => {
    const modelName = openrouterModel.trim();
    if (!modelName) return;

    setModelSaving(true);
    setModelSaved(false);
    try {
      const savedSetting = await api.saveSetting('openrouter_model', modelName);
      setOpenrouterModel(savedSetting.value);
      setModelSaved(true);
    } catch (err) {
      alert('Error saving model: ' + err.message);
    } finally {
      setModelSaving(false);
    }
  };

  if (loading) return <div className={styles.container}>Loading Settings...</div>;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>API Settings</h1>
        <p className={styles.subtitle}>
          Manage your API keys. If a key hits its rate limit, the system will automatically rotate to the next active key.
        </p>
      </div>

      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <div>
            <h2 className={styles.sectionTitle}>LLM Configuration</h2>
            <p className={styles.sectionSubtitle}>OpenRouter model used for agentic gold analysis.</p>
          </div>
          {modelSaved && <span className={styles.savedBadge}>Saved</span>}
        </div>

        <div className={styles.modelForm}>
          <label className={styles.label} htmlFor="openrouter-model">OpenRouter Model</label>
          <div className={styles.modelControls}>
            <input
              id="openrouter-model"
              list="openrouter-model-options"
              type="text"
              className={styles.input}
              value={openrouterModel}
              onChange={(e) => {
                setOpenrouterModel(e.target.value);
                setModelSaved(false);
              }}
              onKeyDown={(e) => e.key === 'Enter' && handleSaveModel()}
              placeholder={DEFAULT_OPENROUTER_MODEL}
            />
            <datalist id="openrouter-model-options">
              {OPENROUTER_MODEL_OPTIONS.map((model) => (
                <option key={model} value={model} />
              ))}
            </datalist>
            <button
              className={styles.btnAdd}
              onClick={handleSaveModel}
              disabled={modelSaving || !openrouterModel.trim()}
            >
              {modelSaving ? 'Saving...' : 'Save'}
            </button>
          </div>
        </div>
      </section>

      <div className={styles.grid}>
        {PROVIDERS.map((provider) => {
          const providerKeys = keys[provider.id] || [];
          
          return (
            <div key={provider.id} className={styles.card}>
              <div className={styles.cardHeader}>
                <span className={styles.providerName}>{provider.name}</span>
                <span className={styles.keyCount}>{providerKeys.length} Keys</span>
              </div>

              <div className={styles.keyList}>
                {providerKeys.length === 0 ? (
                  <p style={{ color: '#a0aec0', fontSize: '0.9rem' }}>No keys configured. Will fallback to .env variables if available.</p>
                ) : (
                  providerKeys.map(k => (
                    <div key={k.id} className={styles.keyItem}>
                      <div className={styles.keyHeader}>
                        <div>
                          <span className={`${styles.keyBadge} ${k.is_active ? styles.badgeActive : styles.badgeExhausted}`}>
                            {k.is_active ? 'Active' : 'Exhausted'}
                          </span>
                          {k.is_primary === 1 && (
                            <span className={`${styles.keyBadge} ${styles.badgePrimary}`}>Primary</span>
                          )}
                        </div>
                      </div>
                      
                      <div className={styles.keyValue}>{k.key_value}</div>
                      
                      <div className={styles.keyActions}>
                        {!k.is_active && (
                          <button onClick={() => handleReactivate(k.id)} className={styles.btnSmall}>
                            Reactivate
                          </button>
                        )}
                        <button onClick={() => handleDelete(k.id)} className={`${styles.btnSmall} ${styles.btnDelete}`}>
                          Delete
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>

              <div className={styles.addForm}>
                <input 
                  type="text" 
                  className={styles.input} 
                  placeholder="Enter new API key..." 
                  value={newKeyValues[provider.id] || ''}
                  onChange={(e) => setNewKeyValues({...newKeyValues, [provider.id]: e.target.value})}
                  onKeyDown={(e) => e.key === 'Enter' && handleAddKey(provider.id)}
                />
                <button className={styles.btnAdd} onClick={() => handleAddKey(provider.id)}>Add</button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
