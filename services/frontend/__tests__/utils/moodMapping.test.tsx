import { moodToInt, intToMood, getMoodConfig } from '@/utils/moodMapping'

describe('Mood Mapping Utils', () => {
    test('converts mood string to integer', () => {
        expect(moodToInt('happy')).toBe(7)
        expect(moodToInt('sad')).toBe(3)
        expect(moodToInt('neutral')).toBe(5)
    })

    test('converts integer to mood string', () => {
        expect(intToMood(7)).toBe('happy')
        expect(intToMood(3)).toBe('sad')
        expect(intToMood(5)).toBe('neutral')
    })

    test('gets mood config', () => {
        const config = getMoodConfig('happy')
        expect(config.label).toBe('Happy')
        expect(config.emoji).toBe('😊')
        expect(config.value).toBe(7)
    })
})