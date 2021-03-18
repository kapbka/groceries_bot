class Solution:
    def createTargetArray(self, nums, index):
        res = []
        for i, v in enumerate(nums):
            if len(res) > index[i]:
                res = res[0: index[i]] + [v] + res[index[i]:]
            else:
                res.append(v)
            print(res)
        return res


if __name__ == '__main__':
    s = Solution()
    s.createTargetArray([0,1,2,3,4], [0,1,2,2,1])