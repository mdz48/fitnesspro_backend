import asyncio
from typing import List, Dict, Any, Union
from deep_translator import GoogleTranslator
from app.services.cache_service import cache

class TranslationService:
    def __init__(self, source: str = 'en', target: str = 'es'):
        self.translator = GoogleTranslator(source=source, target=target)
        self.cache_ttl = 86400 * 30  # Cachear traducciones por 30 días

    def _get_translation_from_cache(self, text: str) -> str:
        cache_key = f"trans_{text}"
        return cache.get("translation", cache_key)
        
    def _save_translation_to_cache(self, text: str, translated: str):
        cache_key = f"trans_{text}"
        cache.set("translation", translated, self.cache_ttl, cache_key)

    def _translate_batch_sync(self, texts: List[str]) -> List[str]:
        """Traduce una lista de textos de forma sincrona, usando cache"""
        if not texts:
            return texts
            
        results = []
        to_translate = []
        to_translate_indices = []
        
        for i, text in enumerate(texts):
            if not text or not isinstance(text, str):
                results.append(text)
                continue
                
            cached = self._get_translation_from_cache(text)
            if cached:
                results.append(cached)
            else:
                results.append(None)
                to_translate.append(text)
                to_translate_indices.append(i)
                
        if to_translate:
            try:
                # deep-translator usa chunks por debajo para evitar límites
                translated_batch = self.translator.translate_batch(to_translate)
                for idx, orig, trans in zip(to_translate_indices, to_translate, translated_batch):
                    results[idx] = trans
                    self._save_translation_to_cache(orig, trans)
            except Exception as e:
                # Fallback to original if translation fails
                print(f"Translation error: {e}")
                for idx, orig in zip(to_translate_indices, to_translate):
                    results[idx] = orig
                    
        return results

    async def translate_text(self, text: str) -> str:
        """Traduce un texto individual de forma asincrona"""
        if not text:
            return text
            
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, self._translate_batch_sync, [text])
        return results[0] if results else text

    async def translate_list(self, texts: List[str]) -> List[str]:
        """Traduce una lista de textos"""
        if not texts:
            return []
            
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._translate_batch_sync, texts)

    async def translate_exercise(self, exercise: Dict[str, Any]) -> Dict[str, Any]:
        """Traduce los campos de un solo ejercicio"""
        if not exercise:
            return exercise
            
        translated_exec = exercise.copy()
        
        # Obtenemos todos los strings que necesitamos traducir
        texts_to_translate = []
        
        if 'name' in translated_exec and translated_exec['name']:
            texts_to_translate.append(translated_exec['name'])
            
        list_fields = ['targetMuscles', 'bodyParts', 'equipments', 'secondaryMuscles', 'instructions']
        for field in list_fields:
            if field in translated_exec and isinstance(translated_exec[field], list):
                texts_to_translate.extend(translated_exec[field])
                
        # Traducimos todo en batch
        if texts_to_translate:
            loop = asyncio.get_event_loop()
            translated_texts = await loop.run_in_executor(None, self._translate_batch_sync, texts_to_translate)
            
            # Reasignamos
            idx = 0
            if 'name' in translated_exec and translated_exec['name']:
                translated_exec['name'] = translated_texts[idx]
                idx += 1
                
            for field in list_fields:
                if field in translated_exec and isinstance(translated_exec[field], list):
                    count = len(translated_exec[field])
                    translated_exec[field] = translated_texts[idx:idx+count]
                    idx += count
                    
        return translated_exec

    async def translate_exercise_data(self, data: Any) -> Any:
        """Traduce los ejercicios en la respuesta (data puede ser lista o dict)"""
        # Si es un solo ejercicio (get by id)
        if isinstance(data, dict) and 'name' in data:
            return await self.translate_exercise(data)
            
        # Si es una lista de ejercicios
        if isinstance(data, list):
            tasks = [self.translate_exercise(ex) for ex in data]
            return await asyncio.gather(*tasks)
            
        return data

# Singleton instance
translation_service = TranslationService()
